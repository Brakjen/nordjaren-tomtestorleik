import layout
import pandas as pd
from maindash import app

from globals import DATA

import callbacks

APP_TITLE = "Tomtestorleikar i Rogaland"

def main():
    app.title = APP_TITLE
    app.layout = layout.render(DATA)
    return app.server


if __name__ == "__main__":
    main()
    app.run(debug=True)
