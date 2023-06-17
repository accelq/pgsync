from pgsync import plugin
import datetime;

class CleanScenarioFields(plugin.Plugin):
    name = 'CleanScenarioField'

    def transform(self, doc, **kwargs):
        # deletes
        del doc['test_type_pid']
        del doc['pj_pid']
        del doc['mv_pid']
        del doc['created_user']
        del doc['last_modified_user']
        del doc['status_pid']
        del doc['cross_project_sharing_type_pid']
        del doc['metadata_value']['pj_pid']
        del doc['metadata_value']['project']
        scn_type = doc['test_type']['test_type']
        doc['test_type']['type'] = scn_type
        del doc['test_type']['test_type']
        
        # additions
        doc['project']['is_deleted'] = doc['project']['deleted_timestamp'] != None

        # transforms
        firstname = doc['user_created']['user_fname']
        lastname = doc['user_created']['user_lname']
        doc['user_created']['name'] = f'{firstname} {lastname}'
        firstname = doc['user_last_modified']['user_fname']
        lastname = doc['user_last_modified']['user_lname']
        doc['user_last_modified']['name'] = f'{firstname} {lastname}'
        doc['timestamp'] = datetime.datetime.now()

        if doc['traceability'] != None:
            for index, _ in enumerate(doc['traceability']):
                del doc['traceability'][index]['work_item']['pid']
                for key, value in doc['traceability'][index]['work_item'].items():
                    doc['traceability'][index][key] = value
                del doc['traceability'][index]['work_item']
                del doc['traceability'][index]['scn_pid']
                del doc['traceability'][index]['ext_int_work_item_pid']
        
        if doc['conf_metadata'] != None:
            doc['conf_metadata'] = list(filter(lambda x: x['conf_entity_metadata'] != None, doc['conf_metadata']))
            for index, _ in enumerate(doc['conf_metadata']):
                doc['conf_metadata'][index]['conf_entity_metadata'] = list(filter(lambda x: x['lu_top_entity_type']['entity_name'].lower() == 'scenario' or x['lu_top_entity_type']['entity_name'].lower() == 'manual scenario', doc['conf_metadata'][index]['conf_entity_metadata']))
            doc['conf_metadata'] = list(filter(lambda x: len(x['conf_entity_metadata']) != 0, doc['conf_metadata']))
            doc['custom_fields'] = []
            for _, confMetadata in enumerate(doc['conf_metadata']):
                for _, confEntityMetadata in enumerate(confMetadata['conf_entity_metadata']):
                    if ((confEntityMetadata['lu_top_entity_type']['entity_name'].lower() == 'scenario' and scn_type.lower() != 'auto') or
                        (confEntityMetadata['lu_top_entity_type']['entity_name'].lower() == 'manual scenario' and scn_type.lower() != 'manual')):
                        continue
                    temp = {}
                    temp['unique_name'] = confMetadata['unique_name']
                    temp['pid'] = confMetadata['pid']
                    temp['label'] = confMetadata['label']
                    temp['is_required'] = confMetadata['is_required']
                    temp['db_column_name'] = confEntityMetadata['db_column_name']
                    temp['value'] = doc['metadata_value'][confEntityMetadata['db_column_name']]
                    doc['custom_fields'].append(temp)
            
        # delete duplicates
        del doc['user_created']['user_fname']
        del doc['user_created']['user_lname']
        del doc['user_last_modified']['user_fname']
        del doc['user_last_modified']['user_lname']
        del doc['metadata_value']
        del doc['conf_metadata']
        del doc['_meta']
        return doc