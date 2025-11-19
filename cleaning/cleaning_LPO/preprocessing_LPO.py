from cleaning.utils.constant_settings import (id_espece_cd_nom_dict, mapping_localisation, mapping_full_form,
                                              mapping_estimation_code, mapping_code_atlas_faune,
                                              used_columns, TRANS_GN)
from unidecode import unidecode
from datetime import date

import datetime as dt
import pandas as pd
import numpy as np

import uuid
import re


class Preprocessing_faune():
    def __init__(self, exports):
        self.exports = exports

    def _get_missing_columns(self):
        for col in used_columns:
            if col not in self.stacked_export.columns:
                self.stacked_export[col] = np.nan

    def _remove_slash_separator_inside_parentheses(self):
        """
        Removing unnecessary slashes in the detail column since they are used for separation.        
        """
        self.stacked_export["DETAIL"] = [re.sub(r'(?<=\S)\s*/\s*(?=\S)(?!\s*\d+x)', '-', detail_string) 
                                        if isinstance(detail_string, str) 
                                        else np.nan for detail_string in self.stacked_export["DETAIL"]]  
    
    def _correct_code_atlas_column_name(self):
        if "CODE_ATLAS" in self.stacked_export.columns :
            self.stacked_export.rename(columns = {"CODE_ATLAS" : "ATLAS_CODE"}, inplace = True)

    def _parse_time(self, timing):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return pd.to_datetime(timing, format=fmt).time()
            except ValueError:
                continue
        return None  # Handle invalid formats if any

    # Convertir en timedelta
    def _time_to_timedelta(self, t):
        return dt.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)    
    
    def drop_french_colnames(self):
        # Drop of french colnames    
        for export in self.exports:
            export.drop([0], axis=0, inplace=True)
            export.reset_index(drop=True)
        return self

    def stacking_export(self):
        if len(self.exports) == 1:
            self.stacked_export = self.exports[0]
            self.raw_stacked_export = self.stacked_export.copy()
            self._correct_code_atlas_column_name()
            self._get_missing_columns()
            self._remove_slash_separator_inside_parentheses()
            self.stacked_export["DETAIL"] = self.stacked_export["DETAIL"].fillna("")
            return self.stacked_export
        else:
            self.stacked_export = pd.concat(self.exports, ignore_index = True)
            self.raw_stacked_export = self.stacked_export.copy()
            self._correct_code_atlas_column_name()
            self._get_missing_columns()
            self._remove_slash_separator_inside_parentheses()
            self.stacked_export["DETAIL"] = self.stacked_export["DETAIL"].fillna("")
            return self.stacked_export

    def _get_individual_count(self):
        # Récupère le nombre d'individus devant chaque x dans la colonne détail
        ind_count = [re.findall(r'(\d+)x', detail_string) if detail_string 
                else "" for detail_string in self.stacked_export["DETAIL"]]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("TOTAL_COUNT") + 1, 
                                    "IND_COUNT_LIST", ind_count)
        return self

    def _get_sum_individual_count(self):
        sum_ind_count = [sum(int(nombre) for nombre in nombres_list) 
                if isinstance(nombres_list, list) else np.nan 
                for nombres_list in self.stacked_export["IND_COUNT_LIST"]]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("IND_COUNT_LIST") + 1, 
                                    "SUM_IND_COUNT", sum_ind_count)
        return self

    def _get_diff_total_count_sum_ind_count(self):
        diff_total_count_sum_ind = [
            total_count - sum_ind_count 
            if sum_ind_count is not np.nan else np.nan 
            for total_count, sum_ind_count 
            in zip(
                self.stacked_export["TOTAL_COUNT"], 
                self.stacked_export["SUM_IND_COUNT"]
                )
                ]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("SUM_IND_COUNT") + 1, 
                                    "DIFF_TOT_SUM_IND", diff_total_count_sum_ind)
        return self

    def corrected_detail(self):
        """
        We count the number of known individuals 
        in the column detail to compare it with the total count of individuals, 
        in order to get the unknown individuals before splitting
        """
        self._get_individual_count()
        self._get_sum_individual_count()
        self._get_diff_total_count_sum_ind_count()

        detail_corrected =[
            detail_string + " / " + str(int(diff_tot_sum_ind)) + "x Inconnu" if diff_tot_sum_ind > 0 
            else detail_string if detail_string 
            else str(int(total_count)) + "x Inconnu" if not detail_string 
            else np.nan
            for detail_string, diff_tot_sum_ind, total_count in zip(self.stacked_export["DETAIL"], 
                                                            self.stacked_export["DIFF_TOT_SUM_IND"] ,
                                                            self.stacked_export["TOTAL_COUNT"])
            ]
        self.stacked_export["DETAIL"] = detail_corrected
        # We drop this column in str because when saving to excel, a column cannot contains array or list [1, 2, 3, ...]
        self.stacked_export.drop(["IND_COUNT_LIST"], inplace=True, axis=1)
        return self

    def correct_time_start(self):
        time_start = [
                self._parse_time(timing) if ((time_start == dt.time(0,0,0) 
                            or pd.isnull(time_start)) 
                            and not pd.isnull(timing))
                else time_start
                for timing, time_start in zip(
                                                self.stacked_export["TIMING"], 
                                                self.stacked_export["TIME_START"]
                                            )
                ] 
        self.stacked_export["TIME_START"] = time_start
        return self   

    def correct_time_stop(self):
        # TODO : A corriger garder les time_stop non nuls
        # Comme  un objet de type timedelta ne peut pas être directement converti en time, 
        # on utilise datetime.min qui représente  la date et l'heure la plus ancienne 
        # possible qu’un objet datetime peut avoir dans Python
        time_stop = [
            (dt.datetime.min + (self._time_to_timedelta(time_start) + pd.to_timedelta("5 minutes"))).time()
            if (isinstance(project_code_str, str) and "EPOC" in project_code_str) 
            else time_stop if not (pd.isnull(time_stop) or time_stop == dt.time(0,0,0))
            else dt.time(23,59,59)
            for time_start, time_stop, project_code_str in zip(
                        self.stacked_export["TIME_START"], 
                        self.stacked_export["TIME_STOP"],
                        self.stacked_export["PROJECT_CODE"]
                ) 
        ]
        self.stacked_export["TIME_STOP"] = time_stop
        return self

    def adding_date_max(self):
        date_max = [
                default_date + dt.timedelta(days=1) if time_stop < time_start 
                else default_date 
                for default_date, time_start, time_stop in zip(
                        self.stacked_export["DATE"],
                        self.stacked_export["TIME_START"],
                        self.stacked_export["TIME_STOP"]
                        )
                ]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("DATE") + 1, "DATE_MAX", date_max)
        return self

    def spliting_lines(self):
        # ADD COUNT COLUMN NUMBER OF SPLIT :
        # ENCODED AS 1 : 0 SPLIT (1 individu = 0 split)
        #            2 : 1 SPLIT (2 individus = 1 split)
        #            3 : 2 SPLIT (3 individus = 2 split)
        #                                        etc ...
        self.stacked_export["DETAIL"] = self.stacked_export["DETAIL"].str.split("/")
        self.stacked_export["COUNT"] = [len(list_detail) if list_detail is not np.nan 
                                                else 1 for list_detail in self.stacked_export["DETAIL"]]
    
        self.stacked_export = self.stacked_export.explode("DETAIL")
        self.stacked_export["DETAIL"] = self.stacked_export["DETAIL"].str.strip()
        return self

    def adding_id_sighting_new(self):
        # ADD COLUMN RN USED FOR CREATING ID_SIGTHING_NEW
        self.stacked_export["RN"] = self.stacked_export.groupby(self.stacked_export.index).cumcount()+1
        self.stacked_export.reset_index(drop=True, inplace = True)
        self.stacked_export["ID_SIGHTING_NEW"] = [id_sighting + '-' + str(rn) if count > 1 else id_sighting
            for id_sighting, rn, count in zip(self.stacked_export["ID_SIGHTING"], 
                                        self.stacked_export["RN"], 
                                        self.stacked_export["COUNT"])
                                  ]
        return self

    def adding_ind_count(self):
        ind_count_fin = [
                            int(re.findall(r'\d+', detail_string)[0]) 
                            if isinstance(detail_string, str) 
                            else np.nan for detail_string in self.stacked_export["DETAIL"]
                        ]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("TOTAL_COUNT") + 1, 
                        "IND_COUNT", ind_count_fin)
        return self

    def adding_cd_nom(self):
        self.stacked_export.insert(self.stacked_export.columns.get_loc("ID_SPECIES")+1,
                                   "CD_NOM", self.stacked_export["ID_SPECIES"].map(id_espece_cd_nom_dict) 
        )
        return self

    def adding_uuid(self):
        uuids = [str(uuid.uuid4()) for i in np.arange(len(self.stacked_export))]
        self.stacked_export.insert(0, "UUID", uuids)
        return self

    def adding_precision_enc(self):
        self.stacked_export.insert(self.stacked_export.columns.get_loc("PRECISION") + 1, 
        "PRECISION_ENC", self.stacked_export["PRECISION"].map(mapping_localisation)) 
        return self
    
    def adding_full_form_enc(self):
        self.stacked_export.insert(self.stacked_export.columns.get_loc("FULL_FORM") + 1, 
        "FULL_FORM_ENC", self.stacked_export["FULL_FORM"].map(mapping_full_form)) 
        return self

    def adding_estimation(self):
        # ESTIMATION is equivalent to type_denombrement french colname
        self.stacked_export.insert(self.stacked_export.columns.get_loc("ESTIMATION_CODE") + 1, 
                    "ESTIMATION", self.stacked_export["ESTIMATION_CODE"].map(mapping_estimation_code))
        return self

    def mapping_to_gn_code_atlas(self):
        code_atlas_gn = self.stacked_export["ATLAS_CODE"]\
                    .astype(str).map(mapping_code_atlas_faune)
        self.stacked_export.insert(self.stacked_export.columns.get_loc("ATLAS_CODE") + 1, "ATLAS_CODE_GN", code_atlas_gn)
        return self

    def adding_code_atlas_transcription(self):
        litteral_code_atlas_gn = self.stacked_export["ATLAS_CODE_GN"].map(TRANS_GN)    
        self.stacked_export.insert(self.stacked_export.columns.get_loc("ATLAS_CODE_GN") + 1, 
                    "ATLAS_CODE_TRANSCRIPTION", litteral_code_atlas_gn)
        return self

    def adding_sexe(self):
        sexe_list = [
            "Type femelle" if isinstance(detail_string, str) and "type femelle" in unidecode(detail_string).lower() 
            else "Femelle" if isinstance(detail_string, str) and "femelle" in unidecode(detail_string).lower() 
            else "Mâle" if (isinstance(detail_string, str) and "male" in unidecode(detail_string).lower())
            else np.nan for detail_string in self.stacked_export["DETAIL"]
            ]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("DETAIL") + 1, 
                    "SEXE", 
                    sexe_list)
        return self

    def replace_comma_by_dot_in_coord(self):
       self.stacked_export["COORD_LAT"] =  self.stacked_export["COORD_LAT"]\
                            .astype(str).str.replace(",", ".")
       self.stacked_export["COORD_LON"] =  self.stacked_export["COORD_LON"]\
                            .astype(str).str.replace(",", ".")
       return self
    
    def adding_counting_object(self):
        # La colonne COUNTING_OBJECT => Objet du Dénombrement en anglais
        counting_object = [
            "Pontes" if isinstance(detail_string, str) and re.search(r"(pontes|ponte)", unidecode(detail_string).lower())
            else "Individu"
            for detail_string in self.stacked_export["DETAIL"]
        ]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("DIFF_TOT_SUM_IND") + 1, "COUNTING_OBJECT", counting_object)
        return self

    def adding_biological_state(self):
        biological_state = [
            "Trouvé mort - autre" if isinstance(has_death_info_str, str) 
                        and "oui" in unidecode(has_death_info_str).lower() 
            else "Observé vivant" if isinstance(has_death_info_str, str) 
                        and "non" in unidecode(has_death_info_str).lower()
            else np.nan for has_death_info_str in self.stacked_export["HAS_DEATH_INFO"]
        ] 
        self.stacked_export.insert(self.stacked_export.columns.get_loc("COUNTING_OBJECT") + 1, 
                        "BIOLOGICAL_STATE", biological_state)
        return self

    def adding_observation_status(self):
        # Mapper sur le code atlas Faune
        observation_status = [
            "Non observé" if code_atlas == '99' 
            else "Présent" if code_atlas != '99'
            else np.nan
            for code_atlas in self.stacked_export["ATLAS_CODE"].astype(str)
        ]

        self.stacked_export.insert(self.stacked_export.columns.get_loc("BIOLOGICAL_STATE") + 1, 
                        "OBSERVATION_STATUS", observation_status)
        return self

    def adding_biological_status(self):
        # Mapper une fois le code_atlas mapper sur celui de GeoNatIDF
        biological_status = [
            "Reproduction" if (isinstance(behaviour_string, str) and re.search(r"(accouplement|reproduction|ponte|pontes)", unidecode(behaviour_string).lower())) 
                                or (pd.isnull(behaviour_string) and isinstance(detail_string, str) and re.search(r"(ponte|pontes|larve|tetard)", unidecode(detail_string).lower())) 
                                
            else "Hibernation" if isinstance(behaviour_string, str) and re.search(r"(hiberne|hivernage|hibernation)", unidecode(behaviour_string).lower())
            else "Estivage" if isinstance(behaviour_string, str) and "estivage" in unidecode(behaviour_string).lower()
            else code_atlas if code_atlas is not np.nan 
            else np.nan 
            for code_atlas, behaviour_string, detail_string in zip(
                    self.stacked_export["ATLAS_CODE_GN"], 
                    self.stacked_export["BEHAVIOUR"],
                    self.stacked_export["DETAIL"]
            )
            ]
        # Insérer les résultats dans la dataframe
        self.stacked_export.insert(self.stacked_export.columns.get_loc("OBSERVATION_STATUS") + 1, 
                               "BIOLOGICAL_STATUS", biological_status)
        return self

    def insert_observer(self):
        # NAME : Nom, SURNAME : Prénom
        observer = [
            "Import LPO îdF Anonyme" if (isinstance(surname, str) and isinstance(name, str)) and
                                        (
                                            re.search(r"anonyme", unidecode(name).lower()) or 
                                            re.search(r"anonyme", unidecode(surname).lower())
                                        )
            else " ".join(
                [
                    re.sub(
                        r'(LPO|lpo|lpo Idf|Lpo38|Lpo|idf|IDF|Lpo Bfc|Idf|Bfc)', '', 
                                re.sub(r"[@#()_'%^&{}~&*]", '', name).replace("$", "s")\
                                                                     .replace("/", "")
                    ).strip(), 
                    re.sub(
                        r'(LPO|lpo|lpo Idf|Lpo38|Lpo|idf|IDF|Lpo Bfc|Idf|Bfc)', '', 
                                re.sub(r"[@#()_'%^&{}~&*]", '', surname).replace("$", "s")\
                                                                        .replace("/", "")
                    ).strip()
                ]
            ) if isinstance(surname, str) and isinstance(name, str) 
                                       
            else np.nan
            for surname, name in zip(self.stacked_export["SURNAME"], 
                                            self.stacked_export["NAME"])
            ]

        self.stacked_export.insert(self.stacked_export.columns.get_loc("UUID") + 1, 
                                        "OBSERVER", observer)
        return self

    def adding_life_stage(self):
        # TODO : Simplify code (if else statement)
        # Hint: Dict mapping, apply, assign ..

        life_stage_list = ["Adulte" if (isinstance(detail_string, str) and "adulte" in unidecode(detail_string).lower()) 
        else "Alevin" if (isinstance(detail_string, str) and "alevin" in unidecode(detail_string).lower())          
        else "Bulbe" if (isinstance(detail_string, str) and "bulbe" in unidecode(detail_string).lower())
        else "Chenille" if (isinstance(detail_string, str) and "chenille" in unidecode(detail_string).lower()) 
        else "Chrysalide" if (isinstance(detail_string, str) and "chrysalide" in unidecode(detail_string).lower())
        else "Emergent" if (isinstance(detail_string, str) and "emergent" in unidecode(detail_string).lower())
        else "Exuvie" if (isinstance(detail_string, str) and "exuvie" in unidecode(detail_string).lower())
        else "Fané" if (isinstance(detail_string, str) and "fane" in unidecode(detail_string).lower())
        else "Fruit" if (isinstance(detail_string, str) and "fruit" in unidecode(detail_string).lower())
        else "Germination" if (isinstance(detail_string, str) and "germination" in unidecode(detail_string).lower())
        else "Graine" if (isinstance(detail_string, str) and "graine" in unidecode(detail_string).lower())
        else "Imago" if (isinstance(detail_string, str) and "imago" in unidecode(detail_string).lower())
        else "Immature" if (isinstance(detail_string, str) and "immature" in unidecode(detail_string).lower())
        else "Inconnu" if (isinstance(detail_string, str) and "inconnu" in unidecode(detail_string).lower())
        else "Juvénile" if (isinstance(detail_string, str) and re.search(r"(jeune|jeunes|juvenile)", unidecode(detail_string).lower()))
        else "Larve" if (isinstance(detail_string, str) and "larve" in unidecode(detail_string).lower())
        else "Mue" if (isinstance(detail_string, str) and "mue" in unidecode(detail_string).lower())
        else "Nymphe" if (isinstance(detail_string, str) and "nymphe" in unidecode(detail_string).lower())
        else "Oeuf" if (isinstance(detail_string, str) and re.search(r"(oeuf|pontes|ponte)", unidecode(detail_string).lower()))
        else "Poussin" if (isinstance(detail_string, str) and "poussin" in unidecode(detail_string).lower())
        else "Post-Larve" if (isinstance(detail_string, str) and re.search(r"post[- ]?larve", unidecode(detail_string).lower()))
        else "Pupe" if (isinstance(detail_string, str) and "pupe" in unidecode(detail_string).lower())
        else "Rhizome" if (isinstance(detail_string, str) and "rhizome" in unidecode(detail_string).lower())
        else "Sub-adulte"  if (isinstance(detail_string, str) and re.search(r"sub[- ]?adulte", unidecode(detail_string).lower()))
        else "Sub-imago" if (isinstance(detail_string, str) and re.search(r"sub[- ]?imago", unidecode(detail_string).lower()))
        else "Têtard" if (isinstance(detail_string, str) and "tetard" in unidecode(detail_string).lower())
        else "Thalle, protothalle" if (isinstance(detail_string, str) and re.search(r"(proto)?thalle", unidecode(detail_string).lower()))
        else "Tubercule" if (isinstance(detail_string, str) and "tubercule" in unidecode(detail_string).lower())
        
        # -------------------------------- 1er Hiver
        else "1er hiver" if (isinstance(detail_string, str) and re.search(r"1ere\s+annee", unidecode(detail_string).lower()) 
                             and date(year = export_date.year, month=9, day=23) 
                              <= export_date.date() <= date(year = export_date.year, month=12, day=31))
        else "1er hiver" if (isinstance(detail_string, str) and re.search(r"2eme\s+annee", unidecode(detail_string).lower()) 
                             and date(year = export_date.year, month=1, day=1) 
                              <= export_date.date() <= date(year = export_date.year, month=3, day=20))
        # -------------------------------- 1er Eté        
        else "1er été" if (isinstance(detail_string, str) and re.search(r"2eme\s+annee", unidecode(detail_string).lower())
                           and date(year=export_date.year, month=3, day=20) 
                           <= export_date.date() <= date(year=export_date.year, month=9, day=23))
        # -------------------------------- 2eme Hiver
        else "2ème hiver" if (isinstance(detail_string, str) and re.search(r"2eme\s+annee", unidecode(detail_string).lower())
                             and date(year = export_date.year, month=9, day=23) 
                             <= export_date.date() <= date(year=export_date.year, month=12, day=31))
        else "2ème hiver" if (isinstance(detail_string, str) and re.search(r"3eme\s+annee", unidecode(detail_string).lower())
                             and date(year = export_date.year, month=1, day=1) 
                             <= export_date.date() <= date(year=export_date.year, month=3, day=20))
        # -------------------------------- 2eme Eté
        else "2ème été" if (isinstance(detail_string, str) and re.search(r"3eme\s+annee", unidecode(detail_string).lower())  
                           and date(year=export_date.year, month=3, day=20) 
                           <= export_date.date() <= date(year=export_date.year, month=9, day=23))
        # -------------------------------- 3ème Hiver
        else "3ème hiver" if (isinstance(detail_string, str) and re.search(r"3eme\s+annee", unidecode(detail_string).lower()) 
                              and date(year=export_date.year, month=9, day=23) 
                              <= export_date.date() <= date(year=export_date.year, month=12, day=31))
        else "3ème hiver" if (isinstance(detail_string, str) and re.search(r"4eme\s+annee", unidecode(detail_string).lower()) 
                              and date(year=export_date.year, month=1, day=1) 
                              <= export_date.date() <= date(year=export_date.year, month=3, day=20))
        # -------------------------------- 3ème Eté
        else "3ème été" if (isinstance(detail_string, str) and re.search(r"4eme\s+annee", unidecode(detail_string).lower())  
                            and date(year=export_date.year, month=3, day=20) 
                            <= export_date.date() <= date(year=export_date.year, month=9, day=23))
        # -------------------------------- 4ème Hiver
        else "4ème hiver" if (isinstance(detail_string, str) and re.search(r"4eme\s+annee", unidecode(detail_string).lower()) 
                              and date(year=export_date.year, month=9, day=23) 
                              <= export_date.date() <= date(year=export_date.year, month=12, day=31))  
        else "4ème hiver" if (isinstance(detail_string, str) and re.search(r"5eme\s+annee", unidecode(detail_string).lower()) 
                              and date(year=export_date.year, month=1, day=1) 
                              <= export_date.date() <= date(year=export_date, month=3, day=20))   

        else np.nan for detail_string, export_date in zip(self.stacked_export["DETAIL"], 
                                                        self.stacked_export["DATE"])]

        self.stacked_export.insert(self.stacked_export.columns.get_loc("SEXE") + 1, 
                    "LIFE_STAGE", 
                    life_stage_list)
        return self

    def adding_behaviour_geonat(self):
        behavior_geonat_list = ["Accouplement" if (isinstance(behaviour_string, str) 
                                     and re.search(r"accouplement|reproduction", unidecode(behaviour_string).lower()))
                 else "Chasse / Alimentation" if (isinstance(behaviour_string, str)
                                                 and re.search(r"(en(|\s+)chasse|se(|\s+)nourrit)", unidecode(behaviour_string).lower()))
                 else "Déplacement" if ((isinstance(behaviour_string, str) 
                                         and re.search(r"se\s+deplace", unidecode(behaviour_string).lower())) 
                                         or (isinstance(detail_string, str) 
                                             and re.search(r"en\s+transit", unidecode(detail_string).lower())))
                 else "Dortoir" if (isinstance(behaviour_string, str) 
                                    and re.search(r"dortoir|reposoir", unidecode(behaviour_string).lower()))
                 else "Pond" if (isinstance(behaviour_string, str) 
                                 and "ponte" in unidecode(behaviour_string).lower()) 
                 else "Hivernage" if (isinstance(behaviour_string, str) 
                                 and re.search(r"(hiberne|hivernage)", unidecode(behaviour_string).lower())) 
                 else "Territorial" if (isinstance(behaviour_string, str) 
                                        and re.search(r"(marquage(|\s+)de(|\s+)territoire|defense(|\s+)territoriale)", unidecode(behaviour_string).lower())) 
                 else "Rut / Parades" if ((isinstance(behaviour_string, str) 
                                          and re.search(r"(rut(|\s+)(|/)(|\s+)parade)|(rut|parade)", unidecode(behaviour_string).lower()))
                                          or((pd.isnull(behaviour_string) and isinstance(comment_string, str)) 
                                             and "parade" in unidecode(comment_string).lower()))
                 else "Repos" if (isinstance(behaviour_string, str) 
                                  and re.search(r"se(|\+)repose", unidecode(behaviour_string).lower()))
                 else "Thermo-régulation" if (isinstance(behaviour_string, str) 
                                              and re.search(r"prend(|\s+)((|\s+)|le)(|\s+)soleil", unidecode(behaviour_string).lower()))
                 else "Tandem" if (isinstance(behaviour_string, str) 
                                   and "tandem" in unidecode(behaviour_string).lower())
                 else "Migration" if (isinstance(behaviour_string, str)
                                     and "migration" in unidecode(behaviour_string).lower())
                 else "Estivage" if (isinstance(behaviour_string, str) 
                                     and "estivage" in unidecode(behaviour_string).lower())
                 else "Posé" if (isinstance(behaviour_string, str) 
                                 and "pose" in unidecode(behaviour_string).lower()) 
                                 or (isinstance(detail_string, str) 
                                     and re.search(r"vu(|\s+)pose", unidecode(detail_string).lower()))
                                  or ((pd.isnull(detail_string) and pd.isnull(behaviour_string) and isinstance(comment_string, str))
                                      and re.search(r"(?<!\bpas vu\s)\bpose\b", unidecode(comment_string).lower())) 
                 else "Passage en vol" if (isinstance(detail_string, str)
                                          and re.search(r"en\s+vol", unidecode(detail_string).lower()))
                                           or (pd.isnull(detail_string) and isinstance(comment_string, str) 
                                               and re.search(r"\b(en vol)\b", unidecode(comment_string).lower()))
                 else "Chant" if (isinstance(behaviour_string, str) and re.search(r"(\bchant(e|s|ent)?\b|\bstridule(s|t|nt)?\b)", unidecode(behaviour_string.lower())))
                                or ((pd.isnull(behaviour_string) and isinstance(comment_string, str)) 
                                and re.search(r"(\bchant(e|s|ent)?\b|\bstridule(s|t|nt)?\b)", unidecode(comment_string.lower()))) 
                 else "Cris" if ((isinstance(behaviour_string, str) and "cri" in unidecode(behaviour_string).lower()) 
                                 or (isinstance(comment_string, str) and "cri" in unidecode(comment_string).lower()))
                 else "Colonie" if ((pd.isnull(behaviour_string) and isinstance(comment_string, str)) 
                                    and re.search(r"c(o{1,2}l(o{1,2}n(n{0,1}ie|nie)))", unidecode(comment_string).lower()))
                        
                 else np.nan for behaviour_string, detail_string, comment_string in zip(self.stacked_export["BEHAVIOUR"], 
                                                                        self.stacked_export["DETAIL"], 
                                                                        self.stacked_export["COMMENT"])
        ]
        self.stacked_export.insert(self.stacked_export.columns.get_loc("BEHAVIOUR") + 1, 
                    "BEHAVIOUR_GEONAT", 
                    behavior_geonat_list)
        return self   

    def adding_observation_method(self):
        obs_method_list = [
            "Vu" if (isinstance(detail_string, str) and re.search(r"\((en\s+main)\)|\bvu\b", unidecode(detail_string).lower()))
            else "Vu" if (isinstance(detail_string, str) and re.search(r"\ben\s+vol\b", unidecode(detail_string).lower()) and taxonomy_name == "Oiseaux")
            else "Entendu" if (isinstance(detail_string, str) and "entendu" in unidecode(detail_string).lower()) 
                                 or ((pd.isnull(detail_string) and isinstance(comment_string, str)) 
                                      and re.search(r"\bcontact(|\s+)auditif\b", unidecode(comment_string).lower()))
            else "Vu et entendu" if (isinstance(comment_string, str) 
                             and re.search(r"vu(|\s+)(|et)(|\s+)entendu", unidecode(comment_string).lower()))

            else "Vu en vol / déplacement" if (isinstance(detail_string, str) 
                                            and (re.search(r"\ben\s+vol\b", unidecode(detail_string).lower()) and taxonomy_name == "Chiroptères"))
                                            or ((pd.isnull(detail_string) and isinstance(comment_string, str)) 
                                                and re.search(r"\ben\s+vol\b", unidecode(comment_string).lower()) and taxonomy_name == "Chiroptères")
            else np.nan for detail_string, comment_string, taxonomy_name in zip(
                                                                                self.stacked_export["DETAIL"], 
                                                                                self.stacked_export["COMMENT"], 
                                                                                self.stacked_export["TAXONOMY_NAME"]
                                                                                )
        ]

        self.stacked_export.insert(
                    self.stacked_export.columns.get_loc("DETAIL") + 1, 
                    "OBSERVATION_METHOD", 
                    obs_method_list)  
        return self 

    
        
    def adding_comment_obs(self):
        comment_obs_list = [
        "Comment = " + comment if isinstance(comment, str) else np.nan 
        for comment in self.stacked_export["COMMENT"] 
        ]
        self.stacked_export.insert(
                    self.stacked_export.columns.get_loc("COMMENT") + 1, 
                    "COMMENT_OBSERVATION", 
                    comment_obs_list)
        return self

    def adding_comment_form(self):
        comment_id_form_list = [
            "ID Liste = " + str(id_form) if id_form > 0 else np.nan
            for id_form in self.stacked_export["ID_FORM"]  
            ]    
        self.stacked_export.insert(
                    self.stacked_export.columns.get_loc("ID_FORM") + 1,
                    "COMMENT_FORM",
                    comment_id_form_list)
        return self

    def adding_comment_media(self):
        comment_media_list = [
            "Contient des médias = " + has_media_string 
            if isinstance(has_media_string, str) else np.nan 
            for has_media_string in self.stacked_export["MEDIA_HAS_MEDIA"]
            ]
        self.stacked_export.insert(
                    self.stacked_export.columns.get_loc("MEDIA_HAS_MEDIA") + 1,
                    "COMMENT_MEDIA",
                    comment_media_list)
        return self

    def adding_comment_obs_form_media(self):
        concat_all_list = [
            (comment_obs + " " + comment_form + " " + comment_media).strip()
            for comment_obs, comment_form, comment_media in zip(
                self.stacked_export["COMMENT_OBSERVATION"].fillna(''), 
                self.stacked_export["COMMENT_FORM"].fillna(''),
                self.stacked_export["COMMENT_MEDIA"].fillna(''))
        ]
        self.stacked_export.insert(
            self.stacked_export.columns.get_loc("COMMENT_MEDIA") + 1,
            "COMMENT_OBS_FORM_MEDIA",
            concat_all_list)
        return self

   


   

