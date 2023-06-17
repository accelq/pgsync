import json
from pgsync import plugin
import traceback

class CleanTestCase(plugin.Plugin):
    name = 'CleanTestCase'

    def isNullOrEmpty(self, value):
        return value == None or value == '' or (type(value) == list and len(value) == 0) or (type(value) == dict and len(value) == 0)
    def transform(self, doc, **kwargs):
        try:
            # variables
            scn_type = doc['scenario']['lu_test_type']['test_type']
            SCN_AUTO = 'auto'
            SCN_MANUAL = 'manual'
            MANUAL_SCENARIO = 'manual scenario'
            SCENARIO = 'scenario'
            DATA_TABLE = 'data table'
            scenario_obj = doc['scenario']

            # deletes
            del doc['scn_pid']
            del doc['mv_pid']
            del doc['scenario']['pj_pid']
            del doc['scenario']['test_type_pid']
            del doc['scenario']['project']['pid']

            # special cases
            if 'traceability' in scenario_obj:
                if scenario_obj['traceability'] != None:
                    for index, _ in enumerate(scenario_obj['traceability']):
                        del scenario_obj['traceability'][index]['work_item']['pid']
                        for key, value in scenario_obj['traceability'][index]['work_item'].items():
                            scenario_obj['traceability'][index][key] = value
                        del scenario_obj['traceability'][index]['work_item']
                        del scenario_obj['traceability'][index]['scn_pid']
                        del scenario_obj['traceability'][index]['ext_int_work_item_pid']
                doc['traceability'] = scenario_obj['traceability']
                del doc['scenario']['traceability']

            if 'conf_metadata' in scenario_obj:
                if scenario_obj['conf_metadata'] != None:
                    scenario_obj['conf_metadata'] = list(filter(lambda x: x['conf_entity_metadata'] != None, scenario_obj['conf_metadata']))
                    for index, _ in enumerate(scenario_obj['conf_metadata']):
                        scenario_obj['conf_metadata'][index]['conf_entity_metadata'] = list(filter(lambda x: x['lu_top_entity_type']['entity_name'].lower() == SCENARIO or x['lu_top_entity_type']['entity_name'].lower() == MANUAL_SCENARIO or x['lu_top_entity_type']['entity_name'].lower() == DATA_TABLE, scenario_obj['conf_metadata'][index]['conf_entity_metadata']))
                    scenario_obj['conf_metadata'] = list(filter(lambda x: len(x['conf_entity_metadata']) != 0, scenario_obj['conf_metadata']))
                    doc['scenario_custom_fields'] = []
                    doc['custom_fields'] = []
                    for _, confMetadata in enumerate(scenario_obj['conf_metadata']):
                        for _, confEntityMetadata in enumerate(confMetadata['conf_entity_metadata']):
                            if (confEntityMetadata['lu_top_entity_type']['entity_name'].lower() == SCENARIO or confEntityMetadata['lu_top_entity_type']['entity_name'].lower() == MANUAL_SCENARIO):
                                if ((confEntityMetadata['lu_top_entity_type']['entity_name'].lower() == SCENARIO and scn_type.lower() != SCN_AUTO) or
                                    (confEntityMetadata['lu_top_entity_type']['entity_name'].lower() == MANUAL_SCENARIO and scn_type.lower() != SCN_MANUAL)):
                                    continue
                                temp = {}
                                temp['unique_name'] = confMetadata['unique_name']
                                temp['pid'] = confMetadata['pid']
                                temp['label'] = confMetadata['label']
                                temp['is_required'] = confMetadata['is_required']
                                temp['db_column_name'] = confEntityMetadata['db_column_name']
                                temp['value'] = scenario_obj['metadata_value'][confEntityMetadata['db_column_name']]
                                doc['scenario_custom_fields'].append(temp)
                            elif (confEntityMetadata['lu_top_entity_type']['entity_name'].lower() == DATA_TABLE):
                                temp = {}
                                temp['unique_name'] = confMetadata['unique_name']
                                temp['pid'] = confMetadata['pid']
                                temp['label'] = confMetadata['label']
                                temp['is_required'] = confMetadata['is_required']
                                temp['db_column_name'] = confEntityMetadata['db_column_name']
                                temp['value'] = doc['metadata_value'][confEntityMetadata['db_column_name']]
                                doc['custom_fields'].append(temp)
                del scenario_obj['conf_metadata']
                del scenario_obj['metadata_value']
                del doc['metadata_value']

            # transforms
            doc['name'] = doc['note']
            del doc['note']
            doc['status'] = doc['active']
            del doc['active']
            doc['test_type'] = doc['scenario']['lu_test_type']['test_type']
            del doc['scenario']['lu_test_type']
            doc['scenario']['name'] = doc['scenario']['scn_name']
            del doc['scenario']['scn_name']
            doc['project'] = doc['scenario']['project']
            del doc['scenario']['project']

            # additions
            doc['project']['is_deleted'] = doc['project']['deleted_timestamp'] != None

            # remove fields which are null or Empty
            keyToRemove = []
            for key, value in doc.items():
                if self.isNullOrEmpty(value):
                    keyToRemove.append(key)
            for key in keyToRemove:
                del doc[key]
                
        except:
            print("Error in CleanTestCase")
            traceback.print_exc()
        finally:
            del doc['_meta']
        return doc