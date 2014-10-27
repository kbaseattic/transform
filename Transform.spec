/*
Transform APIs 


*/

module Transform 
{
    /*You need to use KBase auth service to get the authentication*/
    authentication required;
  
    /* A type string copied from WS spec.
         Specifies the type and its version in a single string in the format
         [module].[typename]-[major].[minor]:
         
         module - a string. The module name of the typespec containing the type.
         typename - a string. The name of the type as assigned by the typedef
                 statement. For external type, it start with “e_”.
         major - an integer. The major version of the type. A change in the
                 major version implies the type has changed in a non-backwards
                 compatible way.
         minor - an integer. The minor version of the type. A change in the
                 minor version implies that the type has changed in a way that is
                 backwards compatible with previous type definitions.
         
         In many cases, the major and minor versions are optional, and if not
         provided the most recent version will be used.
         
         Example: MyModule.MyType-3.1
  */
  typedef string type_string;
  
  
  typedef string shock_id;
  
  /* optional shock_url */
  typedef structure {
      shock_id id;
      string shock_url;
  } shock_ref;
  
  /* Information about a module copied from WS.
          
          list<username> owners - the owners of the module.
          spec_version ver - the version of the module.
          typespec spec - the typespec.
          string description - the description of the module from the typespec.
          mapping<type_string, jsonschema> types - the types associated with this
                  module and their JSON schema.
          mapping<modulename, spec_version> included_spec_version - names of 
                  included modules associated with their versions.
          string chsum - the md5 checksum of the object.
          list<func_string> functions - list of names of functions registered in spec.
          boolean is_released - shows if this version of module was released (and hence can be seen by others).
  typedef structure {
          list<username> owners;
          spec_version ver;
          typespec spec;
          string description;
          mapping<type_string, jsonschema> types;
          mapping<type_string, shock_ref> etypes;
          mapping<type_string, shock_ref> validators; 
          mapping<type_string, shock_ref> transformers; 
          mapping<type_string, shock_ref> importer; 
  
          mapping<modulename, spec_version> included_spec_version;
          string chsum;
          list<func_string> functions;
          boolean is_released;
  } ModuleInfo;
  */
  
  
  typedef structure {
      type_string etype;
      string default_source_url;
      shock_ref script;
      /* mapping<string,string> optional_args; // optarg paramters */
  } Importer;
  
  /*funcdef request_to_register_importer(Importer) returns (string result);
  funcdef release_ importer(Importer) returns (string result);*/
  
  /* @optional url */
  typedef structure {
      type_string etype;
      string url;
      string ws_name;
      string obj_name;
      string ext_source_name;
      /* mapping<string, string> optional_args; // optarg key and values */ 
  } ImportParam;
  
  funcdef import_data(ImportParam) returns (string result);
  
  
  
  typedef structure {
      type_string etype;
      shock_ref validation_script;
  } Validator;
  
  /*
  funcdef request_to_register_validator(Validator) returns (string result);
  funcdef release_validator(Validator) returns (string result);
   */
  
  typedef structure {
      type_string etype;
      shock_ref id;
      /* mapping<string, string> optional_args; // optarg key and values */ 
  } ValidateParam;
  funcdef validate(ValidateParam) returns (list<string> result);
  
  
  
  typedef structure {
      Validator validator;
      type_string kb_type;
      shock_ref translation_script;
  } Uploader;
  
  /*
  funcdef request_to_register_uploader(Uploader) returns (string result);
  funcdef release_uploader(Uploader) returns (string result);
   */
  
  typedef structure {
      type_string etype;
      type_string kb_type;
      shock_ref in_id;
      string ws_name;
      string obj_name;
      /* mapping<string, string> optional_args; // optarg key and values */ 
  } UploadParam;
  funcdef uploader(UploadParam) returns (list<string> result);     
  
  typedef structure {
      type_string kb_type;
      type_string ext_type;
      shock_ref translation_script;
  } Downloader;
  
  /*
  funcdef request_to_register_downloader(Downloader) returns (string result);
  funcdef release_downloader(Downloader) returns (string result);
   */

  typedef structure {
      type_string etype;
      type_string kb_type;
      shock_ref out_id;
      string ws_name;
      string obj_name;
      /* mapping<string, string> optional_args; // optarg key and values */ 
  } DownloadParam;
  funcdef download(DownloadParam) returns (list<string> result);
  
};
