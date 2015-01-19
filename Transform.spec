/*
   Transform Service

   This KBase service supports translations and transformations of data types,
   including converting external file formats to KBase objects, 
   converting KBase objects to external file formats, and converting KBase objects
   to other KBase objects, either objects of different types or objects of the same
   type but different versions.
*/


module Transform 
{
     /* Public service methods that require no authentication. */

     /*
        Returns the service version string.
     */
    funcdef version() returns(string result);


    /*  
       Returns all available service methods, and info about them.
    */
    funcdef methods(string query) returns(list<string>results);


    /* All methods that follow will require authentication. */
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
  
    
    typedef structure {
        string external_type;
        type_string kbase_type;
        mapping<string,string> url_mapping;
        string workspace_name;
        string object_name;
        string object_id;
        string options; /* json string */
    } UploadParameters;
    
    funcdef upload(UploadParameters args) returns (list<string> result);     

  
    typedef structure {
        type_string kbase_type;
        string external_type;
        string workspace_name;
        string object_name;
        string object_id;
        string options; /* json string*/
    } DownloadParameters;
    
    funcdef download(DownloadParameters args) returns (list<string> result);


    /*
       Method convert:

       This method provides the capability to convert between two KBase object types.
    */

    typedef structure {
        type_string source_kbase_type;
        string source_workspace_name;
        string source_object_name;
        string source_object_id;
        type_string destination_kbase_type;
        string destination_workspace_name;
        string destination_object_name;
        string destination_object_id;
        string options; /* json string*/
    } ConvertParameters;
    
    funcdef convert(ConvertParameters args) returns (list<string> result);

};
