from cleaning.utils.reading_saving_data import read_exports, style_and_save
from cleaning.utils.utils_webapp import get_upload_LPO_file_list, CLEANED_FOLDER_LPO
from cleaning.cleaning_LPO.preprocessing_LPO import Preprocessing_faune


def main():
    # Setting variables
    LPO_file_list = get_upload_LPO_file_list()
    exports_list = read_exports(LPO_file_list)
    # Preprocessing
    preprocessing_faune = Preprocessing_faune(exports_list)
    preprocessing_faune.drop_french_colnames()
    preprocessing_faune.stacking_export()
    preprocessing_faune.replace_comma_by_dot_in_coord()
    preprocessing_faune.corrected_detail()
    preprocessing_faune.correct_time_start()
    preprocessing_faune.correct_time_stop()
    preprocessing_faune.adding_date_max()
    preprocessing_faune.spliting_lines()
    preprocessing_faune.adding_id_sighting_new()
    preprocessing_faune.adding_ind_count()
    preprocessing_faune.adding_uuid()
    preprocessing_faune.adding_cd_nom()
    preprocessing_faune.adding_precision_enc()
    preprocessing_faune.adding_full_form_enc()
    preprocessing_faune.adding_estimation()
    preprocessing_faune.mapping_to_gn_code_atlas()
    preprocessing_faune.adding_code_atlas_transcription()
    preprocessing_faune.adding_sexe()
    preprocessing_faune.adding_life_stage()
    preprocessing_faune.adding_behaviour_geonat()
    preprocessing_faune.adding_observation_method()
    preprocessing_faune.adding_counting_object()
    preprocessing_faune.adding_biological_state()
    preprocessing_faune.adding_observation_status()
    preprocessing_faune.adding_biological_status()
    preprocessing_faune.adding_comment_obs()
    preprocessing_faune.adding_comment_form()
    preprocessing_faune.adding_comment_media()
    preprocessing_faune.insert_observer()
    return preprocessing_faune.stacked_export, preprocessing_faune.raw_stacked_export