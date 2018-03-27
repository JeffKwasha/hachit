Current Goals for v1.0:
* locations can reference inputs AND docs
* Documentation (is it realistic to think anyone understands Mapper from looking at plugins?)
* cleanup Plugins for release
	* release plugins should exhibit all features:
		* Mapper DISCARD
		* Mapper REMAP
		* Mapper eval_fields
		* Lambda functions
		* local module functions
		* neighbor imports
		* neighbor data files
* Prevent plugin cycles
* display helpful errors

Future Features:
* merge results instead of 'dict.update()'
* Cache Ageing and updates
* Rate limiting
* Better error messages for plugins
	* make api_input's error field more... universal
* Statistics (to prove this is all actually useful)
* RESTful input improvements
	* authentication support
	* Cache failed responses with a separate timeout
* More Inputs and Plugins
	* proper elasticsearch input (elasticcache will technically work, but isn't automatic... etc)
	* XML input
	* DB input
	* Splunk API plugin
	* non-json web API inputs
	* more Emerging Threats API plugins
	* DomainTools plugin
	* PassiveTotal plugin
* Elastic Search improvements: 
    * Automatic handling/re-indexing when plugins change field types
    * Specifying field types and analyzers might provide secondary utility
    * Possibly 'cleaup' of old unused records
