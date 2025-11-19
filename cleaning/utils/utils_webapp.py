import os

dir_path = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(dir_path, "../.."))
cleaning_dir = os.path.abspath(os.path.join(root_dir, "cleaning"))
cleaning_LPO_dir = os.path.abspath(os.path.join(cleaning_dir, "cleaning_LPO"))

# Upload and Cleaned folder to store the raw and cleaned import

UPLOAD_FOLDER_LPO = os.path.abspath(os.path.join(cleaning_LPO_dir , 
                                                    'uploads_LPO'))
CLEANED_FOLDER_LPO =  os.path.abspath(os.path.join(cleaning_LPO_dir , 
                                                    'cleaned_LPO'))
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

list_dir_upload = os.listdir(UPLOAD_FOLDER_LPO)
list_dir_cleaned = os.listdir(CLEANED_FOLDER_LPO)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_LPO_file_list():
    upload_LPO_file_list = [UPLOAD_FOLDER_LPO + "/" + file 
                            for file in os.listdir(UPLOAD_FOLDER_LPO)]
    return upload_LPO_file_list

def remove_files_from_upload_dir(UPLOAD_FOLD):
    if os.listdir(UPLOAD_FOLD):
        for file in os.listdir(UPLOAD_FOLD):
            os.remove(UPLOAD_FOLD + "/" + file)

def read_content_delete_file(CLEANED_FOLD):
    if os.listdir(CLEANED_FOLD):
        with open(CLEANED_FOLD + "/" + "cleaned_LPO_export.xlsx", "rb") as f:
            contents = f.read()
        os.remove(CLEANED_FOLD + "/" + "cleaned_LPO_export.xlsx")
        return contents

def create_colnames_dict(worksheet):
    colnames_index = dict()
    current_col=0
    for col in worksheet.iter_cols(1, worksheet.max_column):
        colnames_index[col[0].value] = current_col
        current_col += 1
    return colnames_index

if __name__ == "__main__":
    remove_files_from_upload_dir(UPLOAD_FOLDER_LPO)
