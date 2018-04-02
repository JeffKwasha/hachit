Current Goals for v1.0:
* locations can reference inputs AND docs
* Documentation (is it realistic to think anyone understands Mapper from looking at plugins?)
* Mapper
	* default 'None' value for REMAP/eval, ie: "" to prevent consumer having to check everything
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
* Rate limiting (all queries require effort, what do we do when an input is 'down'? temporarily / permanently)
* display helpful errors
	* validation: (args -> location, result -> data)
	* temporary failure / permanent failure
	* plugin errors
* Bugs:
	* counter(\*\*kwargs) - somehow this causes api_input to fail \_test()

Future Features:
* merge results instead of 'dict.update()'
* query 'solver' - user supplies one parameter - solver looks up compatible inputs, gets&translates results, queries compatible inputs, LOOP
* automatic look ahead and resolution for selecting a list entry in 'drill down' REMAPs - possibly by looping and checking the recursive return value
* Warnings:
	* Redundant Caching
	* name / filename mismatch
* Cache Ageing and updates
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
