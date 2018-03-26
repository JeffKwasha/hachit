Current Goal:
* locations can reference docs and inputs
* Documentation 
* merge results 
* cleanup Plugins for release
	* Plugins have access to secrets from configuration, utility functions
* Prevent plugin cycles and error gracefully

Future Features:
* Cache Ageing and updates
* Rate limiting
* better error messages for plugins
* statistics
* RESTful input
	* authentication support
	* Cache failed responses with a seperate timeout
* Elastic Search improvements: 
    * Automatic handling/re-indexing when plugins change field types
    * Specifying field types and analyzers might provide secondary utility
    * Possibly 'cleaup' of old unused records
* More Inputs and Plugins
	* XML
	* Splunk API
	* Emerging Threats API
	* DB 
	* non-json web APIs
	* DomainTools
	* PassiveTotal
