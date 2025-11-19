from cleaning.utils.utils_webapp import (UPLOAD_FOLDER_LPO, CLEANED_FOLDER_LPO)
from cleaning.utils.utils_webapp import (remove_files_from_upload_dir, 
                                            read_content_delete_file)
from cleaning.utils.reading_saving_data import style_and_save
from cleaning.cleaning_LPO.main_preprocessing_LPO import main
from flask import (Flask, render_template, request, 
                    send_file, flash, redirect)
from werkzeug.utils import secure_filename
# from waitress import serve

import pandas as pd
import io
import os

if not os.path.isdir(UPLOAD_FOLDER_LPO):
    os.makedirs(UPLOAD_FOLDER_LPO)
if not os.path.isdir(CLEANED_FOLDER_LPO):
    os.makedirs(CLEANED_FOLDER_LPO)



app = Flask(__name__)
app.config['UPLOAD_FOLDER_LPO'] = UPLOAD_FOLDER_LPO
app.config['CLEANED_FOLDER_LPO'] = CLEANED_FOLDER_LPO



@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('file')
        for file in files:
            fn = secure_filename(file.filename)
            try:
                file.save(os.path.join(app.config["UPLOAD_FOLDER_LPO"], fn))
            except Exception as e :
                print(e)
        try : 
            cleaned_export, raw_export = main()
        except Exception as e :
            print(f"Error cleaning data: {e}")
        remove_files_from_upload_dir(UPLOAD_FOLDER_LPO)
        style_and_save(cleaned_export, raw_export, os.path.join(app.config['CLEANED_FOLDER_LPO'], "cleaned_LPO_export.xlsx"))
        contents = read_content_delete_file(CLEANED_FOLDER_LPO)
        return send_file(io.BytesIO(contents),
                            as_attachment=True,
                            download_name="cleaned_LPO_export.xlsx",
                            mimetype="application/vnd.ms-excel"
                            )
    return render_template('index.html')    

def create_app():
    return app 
