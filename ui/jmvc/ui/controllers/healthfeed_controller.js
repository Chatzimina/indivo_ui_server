/**
 * @tag controllers, home
 * 
 * @author Arjun Sanyal (arjun.sanyal@childrens.harvard.edu)
 * @author Ben Adida (ben.adida@childrens.harvard.edu)
 *
 * Displays healthfeed
 *
 */
$.Controller.extend('UI.Controllers.Healthfeed',
/* @Static */
{
},
/* @Prototype */
{
	init: function() {
		steal.dev.log(this.Class.fullName + " init");
		this.account = this.options.account;
	
		var record = this.options.account.attr("activeRecord"); 
		//var record = this.record.id;
		 var self = this;        
        //record = this.options.account.attr("activeRecord");

		//var recordid = this.record.id
		//var xmlHttp = null;
		//xmlHttp = new XMLHttpRequest();
	    	//xmlHttp.open( "GET", "http://www.google.gr", false );
		//xmlHttp.send( null );
		record = this.account.id
	//	 var activeRecord = this.account.attr("activeRecord");
		this.account.get_healthfeed(function(notifications) {
			self.element.html($.View('//ui/views/healthfeed/show.ejs',{'notifications': notifications},{'record':record}));
		});
	}
});
