import os
import argparse
import psycopg2
from urllib import parse
from flask import Flask, redirect, url_for, request, render_template, send_file


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configuration setup
parser = argparse.ArgumentParser()
parser.add_argument("--out", default="out.csv", help='specify the output CSV file')
args = parser.parse_args()

# Parse the DATABASE_URL to get the connection details

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL, sslmode='require')


# Replace the file writing code with PostgreSQL INSERT statements
with conn.cursor() as cur:
    cur.execute(
        """
CREATE TABLE IF NOT EXISTS tablelabels (
    image VARCHAR(255),
    id VARCHAR(255),
    name VARCHAR(255),
    x_min FLOAT,
    x_max FLOAT,
    y_min FLOAT,
    y_max FLOAT
)

        """
    )
conn.commit()

default_directory = "image/directory"  # Set a default directory
app.config["IMAGES"] = default_directory

app.config["LABELS"] = []
files = None

for (dirpath, dirnames, filenames) in os.walk(app.config["IMAGES"]):
    files = filenames
    break

if files is None:
    print("No files")
    exit()

app.config["FILES"] = files
app.config["HEAD"] = 0
app.config["OUT"] = args.out

print(files)

#with open(app.config["OUT"], 'w') as f:
#    f.write("image,id,name,xMin,xMax,yMin,yMax\n")

@app.route('/')
def index():
    return redirect(url_for('tagger'))

@app.route('/tagger')
def tagger():
    if (app.config["HEAD"] == len(app.config["FILES"])):
        return redirect(url_for('bye'))
    directory = app.config['IMAGES']
    image = app.config["FILES"][app.config["HEAD"]]
    labels = app.config["LABELS"]
    not_end = not(app.config["HEAD"] == len(app.config["FILES"]) - 1)
    print(not_end)
    return render_template('tagger.html', not_end=not_end, directory=directory, image=image, labels=labels, head=app.config["HEAD"] + 1, len=len(app.config["FILES"]))

@app.route('/next')
def next():
    image = app.config["FILES"][app.config["HEAD"]]
    app.config["HEAD"] = app.config["HEAD"] + 1
    with conn.cursor() as cur:
        for label in app.config["LABELS"]:
            cur.execute(
                """
                INSERT INTO tablelabels (image, id, name, x_min, x_max, y_min, y_max)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (image, label["id"], label["name"], label["xMin"], label["xMax"], label["yMin"], label["yMax"])
            )
    conn.commit()
    app.config["LABELS"] = []
    return redirect(url_for('tagger'))

@app.route("/bye")
def bye():
    return send_file("taf.gif", mimetype='image/gif')

@app.route('/add/<id>')
def add(id):
    xMin = request.args.get("xMin")
    xMax = request.args.get("xMax")
    yMin = request.args.get("yMin")
    yMax = request.args.get("yMax")
    app.config["LABELS"].append({"id": id, "name": "", "xMin": xMin, "xMax": xMax, "yMin": yMin, "yMax": yMax})
    return redirect(url_for('tagger'))

@app.route('/remove/<id>')
def remove(id):
    index = int(id) - 1
    del app.config["LABELS"][index]
    for label in app.config["LABELS"][index:]:
        label["id"] = str(int(label["id"]) - 1)
    return redirect(url_for('tagger'))

@app.route('/label/<id>')
def label(id):
    name = request.args.get("name")
    app.config["LABELS"][int(id) - 1]["name"] = name
    return redirect(url_for('tagger'))

@app.route('/image/<f>')
def images(f):
    images_directory = "image/directory"
    return send_file(os.path.join(images_directory, f))

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host="0.0.0.0")
