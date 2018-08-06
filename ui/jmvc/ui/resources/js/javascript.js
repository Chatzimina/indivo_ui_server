var isIE = (navigator.appName == "Microsoft Internet Explorer");
var isNetscape = (navigator.appName == "Netscape");
var isOpera = (navigator.appName == "Opera");

function allowOnlyNumber(evt)
{
  var charCode = (evt.which) ? evt.which : event.keyCode
  if (charCode > 31 && (charCode < 48 || charCode > 57))
    return false;
  return true;
}
var error_color = '#FF9494';
function FormValidation(parentElementID) {
    var msg = '';
    var requiredElements = new Array();
    var invalidIntegerElements = new Array();
    var invalidDoubleElements = new Array();
    var invalidEmailElements = new Array();
    var invalidDateElements = new Array();
    var inputs = el(parentElementID).getElementsByTagName('input');
   

    try {
        jQuery('.qtip').remove();
    }
    catch (e) { }
    
    for (var i = 0; i < inputs.length; i++) 
    {
        var inp = inputs[i];

        if ((inp.getAttribute('type') == 'text' || inp.getAttribute('type') == 'password' || inp.getAttribute('type') == 'hidden') &&
            inp.getAttribute('req') == '1') 
        {

            inp.style.backgroundColor = 'white';
            
            if (inp.getAttribute('type') == 'hidden') {
                inp.parentNode.style.backgroundColor = 'white';
            }
            if (inp.value == '') {
                requiredElements[requiredElements.length] = inp;
                inp.style.backgroundColor = error_color;
                addTootip(inp.id, 'This field is mandatory.');
                if (inp.getAttribute('type') == 'hidden') {
                    inp.parentNode.style.backgroundColor = error_color;
                }
            }
            else if (inp.value != '') 
            {
                if (inp.getAttribute('integer') == '1') 
                {
                    //var value_bigger_than = parseFloat(inp.getAttribute('value_bigger_than'));
                    if (!is_int(inp.value))// || parseInt(inp.value) <= value_bigger_than) 
                    {
                        invalidIntegerElements[invalidIntegerElements.length] = inp;
                        inp.style.backgroundColor = error_color;
                        addTootip(inp.id, 'This field accepts integers.');
                    }
                }
                else if (inp.getAttribute('double') == '1') 
                {
                    //var value_bigger_than = parseFloat(inp.getAttribute('value_bigger_than'));
                    if (!is_double(inp.value))// || parseFloat(inp.value) <= value_bigger_than) 
                    {                        
                        invalidDoubleElements[invalidDoubleElements.length] = inp;
                        inp.style.backgroundColor = error_color;
                        addTootip(inp.id, 'This field accepts numbers.');
                    }
                }
                else if (inp.getAttribute('email') == '1') 
                {
                    if (!ValidateEmail(inp.value)) 
                    {
                        invalidEmailElements[invalidEmailElements.length] = inp;
                        inp.style.backgroundColor = error_color;
                        addTootip(inp.id, 'Email is not in the correct format.');
                    }
                }
                else if (inp.getAttribute('date') == '1') 
                {
                    if (!is_date(inp.value)) 
                    {
                        invalidDateElements[invalidDateElements.length] = inp;
                        inp.style.backgroundColor = error_color;
                        addTootip(inp.id, 'Date is not in the correct format.');
                    }
                }
            }
        }
    }

    var textareas = el(parentElementID).getElementsByTagName('textarea');
    for (var i = 0; i < textareas.length; i++) {
        var textarea = textareas[i];
        textarea.style.backgroundColor = 'white'; 
        if (textarea.value == '' && textarea.getAttribute('req') == '1') {
            requiredElements[requiredElements.length] = textarea;
            textarea.style.backgroundColor = error_color;
            addTootip(textarea.id, 'This field is mandatory.');
        }
    }

    var sels = el(parentElementID).getElementsByTagName('select');
    for (var i = 0; i < sels.length; i++) {
        var sel = sels[i];
        sel.style.backgroundColor = 'white'; 
        if (sel.selectedIndex == 0 && sel.getAttribute('req') == '1') {
            requiredElements[requiredElements.length] = sel;
            sel.style.backgroundColor = error_color;
            addTootip(sel.id, 'This field is mandatory.');
        }
    }
 
    var msg = '';
    if (requiredElements.length > 0) {
        msg = 'Please fill in the mandatory fields.\n';
        //msg += requiredElements.length + '\n';
        //msg += requiredElements[0].id + '\n';
        //msg += requiredElements[1].id + '\n';
    }
    if (invalidIntegerElements.length > 0) {
        msg += 'Please fill in the integer fields correctly.\n';
    }
    if (invalidDoubleElements.length > 0) {
        msg += 'Please fill in the decimal fields correctly.\n';
    }
    if (invalidEmailElements.length > 0) {
        msg += 'Please fill in the email fields correctly.\n';
    }
    if (invalidDateElements.length > 0) {
        msg += 'Please fill in the date fields correctly.\n';
    }
    
    return msg;

}

function addTootip(elementID, txt) {
    try {
        jQuery('#' + elementID).qtip(
   {
       content: txt,
       style: {
           //name: 'red' // Inherit from preset style
           backgroundColor: 'red',
           color: 'white',
           fontWeight: 'bold'
       },
       //tip: 'leftMiddle'
       position: {
           corner: {
               target: 'bottomLeft', 
           }
       }
   });
    }
    catch (e) { }
   return false;
}

function ValidURL(s) {
//    var pattern = new RegExp('^(https?:\/\/)?' + // protocol
//    '((([a-z\d]([a-z\d-]*[a-z\d])*)\.)+[a-z]{2,}|' + // domain name
//    '((\d{1,3}\.){3}\d{1,3}))' + // OR ip (v4) address
//    '(\:\d+)?(\/[-a-z\d%_.~+]*)*' + // port and path
//    '(\?[;&a-z\d%_.~+=-]*)?' + // query string
//    '(\#[-a-z\d_]*)?$', 'i'); // fragment locater
//    if (!pattern.test(str)) {
//        //alert("Please enter a valid URL.");
//        return false;
//    } else {
//        return true;
    //    }

    var regexp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
    return regexp.test(s);    
}

function setKey(keyName, keyValue) {
    jQuery.jStorage.set(keyName, keyValue);
}

function getKey(keyName) {
    var result = jQuery.jStorage.get(keyName);
    if (result == null)
        result = '';
    return result;
}

jQuery.fn.center = function() {
    this.css("position", "absolute");
    this.css("top", Math.max(0, ((jQuery(window).height() - jQuery(this).outerHeight()) / 2) +
                                                jQuery(window).scrollTop()) + "px");
    this.css("left", Math.max(0, ((jQuery(window).width() - jQuery(this).outerWidth()) / 2) +
                                                jQuery(window).scrollLeft()) + "px");
    return this;
}


function setCheckBoxes(parentElement, checked) {
    if (!parentElement)
        return false;
        
    var els = parentElement.getElementsByTagName('input');
    for (var i = 0; i < els.length; i++) {
        if (els[i].getAttribute('type') == 'checkbox') {
            els[i].checked = checked;
        }
    }

    return false;
}

String.prototype.trim = function() {
    return this.replace(/^\s+|\s+$/g, '');
}

function hideTooltip() {
    el('divTooltip').style.display = 'none';
    return false;
}

function showTooltip(sender, content) {
    var left = findPosX(sender);
    var top = findPosY(sender);

    var divTooltip = el('divTooltip');
    divTooltip.innerHTML = content;
    divTooltip.style.left = left.toString() + 'px';
    divTooltip.style.top = (top + 28).toString() + 'px';
    divTooltip.style.display = '';
    return false;
}

function tablecards_checkbox_clicked(sender, rowsElement, colsElement) {
    setCheckBoxes(sender.parentNode.parentNode, false);
    sender.checked = true;
    var arr = sender.id.split('_');
    rowsElement.value = arr[arr.length - 2];
    colsElement.value = arr[arr.length - 1];
    //alert(sender.id);
}

function removeElement(parentDiv, childDiv) {
    if (childDiv == parentDiv) {
        alert("The parent div cannot be removed.");
    }
    else if (document.getElementById(childDiv)) {
        var child = document.getElementById(childDiv);
        var parent = document.getElementById(parentDiv);
        parent.removeChild(child);
    }
    else {
        alert("Child div has already been removed or does not exist.");
        return false;
    }
}

function urlParamsArray() {
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

function getUrlParametersForPaging() {
    var params = '';
    if (window.location.href.indexOf('?') > 0)
        params = window.location.href.split('?')[1];
    //alert(params);
    if (params.indexOf('page=') < 0) {
        params = CutEndingChar(params, '&');
        return params;
    }
    else {
        params = params.split('page=')[0];
        params = CutEndingChar(params, '&');
        return params;
    }

    params = CutEndingChar(params, '&');
    return params;
}

function getLocationHref(params, page) {
    var loc = '';
    var cleanUrl = location.href.split('?')[0];
    if (params != '') 
        loc = cleanUrl + '?' + params + '&page=' + page;
    else if (params == '') 
        loc = cleanUrl + '?page=' + page;
    return loc;
}

function gotopage(mode, sender, pageCount, hdnCurrentPage, btnPaging) {
    var page = hdnCurrentPage.value;
    if (mode == 'go') {
        page = sender.value;
    }
    else if (mode == 'first') {
        page = '1';
    }
    else if (mode == 'previous') {
        if (page != '') {
            page = (parseInt(page) - 1).toString();
        }
        if (parseInt(page) <= 0) page = '1';
    }
    else if (mode == 'next') {
        page = (parseInt(page) + 1).toString();
        if (parseInt(page) > parseInt(pageCount))
            page = pageCount;
    }
    else if (mode == 'last') {
        page = pageCount;
    }

    if (parseInt(page) < 0) page = '1';

    hdnCurrentPage.value = page;
    sender.value = page;
    //alert(hdnCurrentPage.id + ", " + hdnCurrentPage.value);
    btnPaging.click();
    return false;
}

function gotopage1(mode, pageCount, hdnCurrentPage, btnPagingID) {
    var page = hdnCurrentPage.value;
    if (mode == 'first') {
        page = '1';
    }
    else if (mode == 'previous') {
        if (page != '') {
            page = (parseInt(page) - 1).toString();
        }
        if (parseInt(page) <= 0) page = '1';
    }
    else if (mode == 'next') {
        page = (parseInt(page) + 1).toString();
        if (parseInt(page) > parseInt(pageCount))
            page = pageCount;
    }
    else if (mode == 'last') {
        page = pageCount;
    }

    if (parseInt(page) < 0) page = '1';

    hdnCurrentPage.value = page;
    
    setTimeout('el("'+btnPagingID+'").click();', 100);
    return false;
}

function windowOnLoad() {
    var dimmerDivHtml = '<div style="-ms-filter: \'progid:DXImageTransform.Microsoft.Alpha(Opacity=80)\';filter: alpha(opacity=80);-moz-opacity: 0.8;-khtml-opacity: 0.8;opacity: 0.8;background-color: #000;z-index: 100;  position: fixed; left: 0px; top: 0px; width: 100%;height: 100%;"></div>'
    var dimmer = document.createElement('div');
    dimmer.style.width = '100%;'
    dimmer.style.height = '100%;'
    
    dimmer.style.position = 'fixed';
    dimmer.style.left = '0px';
    dimmer.style.top = '0px';
    dimmer.style.zIndex = '100';
    dimmer.style.backgroundColor = 'red';
    dimmer.id = 'dimmer';
    dimmer.style.display = 'none';
    dimmer.style.visibility = 'hidden';
    dimmer.innerHTML = dimmerDivHtml;
    document.body.appendChild(dimmer);
    
    if (window.opener && el('menu')) {
        el('menu').style.display = 'none';
        var btnClose = document.createElement('input');
        btnClose.setAttribute('type', 'button');
        btnClose.setAttribute('value', 'Close');
        btnClose.style.fontSize = '20px';
        btnClose.style.fontWeight = 'Bold';
        btnClose.style.width = '200px';
        btnClose.style.height = '50px';
        
        btnClose.onclick = function() { window.close(); };
        document.body.appendChild(document.createElement('br'));
        document.body.appendChild(document.createElement('br'));
        document.body.appendChild(btnClose);
        
    }
}

function toggle(elemID) {
    if (!el(elemID)) return false;
    var dv = el(elemID);
    if (dv.style.display != 'none') {
        dv.style.display = 'none';
        //el('dimmer').style.visibility = 'hidden';
        //el('dimmer').style.display = 'none';
        return false;
    }
    //CenterElement(elemID);
    dv.style.display = '';
    dv.style.zIndex = '200';
    //el('dimmer').style.zIndex = '100';
    //el('dimmer').style.visibility = 'visible';
    //el('dimmer').style.display = '';
    return false;
}

function getCurrentDate() {

    var months = ["Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαϊου", "Ιουνίου", "Ιουλίου",
                "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου"];
    var days = ["Κυριακή", "Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο"];

    var dt = '';
    var currentDate = new Date();
    var day = currentDate.getDate();
    var month = currentDate.getMonth() + 1;
    var year = currentDate.getFullYear();

    var currentTime = new Date();
    var hours = currentTime.getHours().toString();
    if (hours.length == 1) {
        hours = "0" + hours;
    }
    var minutes = currentTime.getMinutes().toString();
    if (minutes.length == 1) {
        minutes = "0" + minutes;
    }

    /*
    if (day < 10) {
    day = "0" + day;
    }

    if (month < 10) {
    month = "0" + month;
    }

    if (hours < 10) {
    hours = "0" + hours;
    }

    if (minutes < 10) {
    minutes = "0" + minutes;
    }
    */
    //dt = "<b>" + day + "/" + month + "/" + year + " " + hours + ":" + minutes + " " + "</b>"
    //dt = day + "/" + month + "/" + year + " " + hours + ":" + minutes

    dt = days[currentDate.getDay()] + ", " + day + " " + months[month - 1] + " " + year; //+ " | " + hours + ":" + minutes;

    return dt;
}

function uploadPhotoPopUp(recid, photo_index, senderid) {
    popup('UploadPhoto.aspx?photo_index=' + photo_index + '&recid=' + recid + '&senderid=' + senderid, 'UploadPhoto', 800, 600, 1);
    return false;
}

function ToggleDlg(sender, divID, leftMargin, topMargin, title) {
    var dv = el(divID);
    if (dv.style.display != 'none') {
        dv.style.display = 'none';
        return false;
    }

    var left = findPosX(sender);
    var top = findPosY(sender);
    if (leftMargin == null || topMargin == null) {
        dv.style.left = '50px';
        dv.style.top = '50px';
    }
    else {
        dv.style.left = (left + leftMargin).toString() + 'px';
        dv.style.top = (top + topMargin).toString() + 'px';
    }
    dv.style.display = '';

    if (title != null) {
        try {
            dv.getElementsByTagName('td')[0].innerHTML = title;
        }
        catch (e) { }
    }
}

function ddl_expand(select) {
    
    return false;
}


var DAYS_ARRAY = new Array('Κυριακή','Δευτέρα','Τρίτη','Τετάρτη','Πέμπτη','Παρασκευή','Σάββατο');
function loadDaysSelectionList(elem)
{

}

var msg = '';
var the_url = '';
function ShowAlert()
{
	alert(msg);
}

function ShowMessageAndRedirect(msg, url) {
    alert(msg);
    if (!url || url == '')
        return false;
    location.href = url;
}

function resetChildElements(parentID) {
    var parentEl = el(parentID);
    var inputs = parentEl.getElementsByTagName('input');
    var inputsCount = inputs.length;
    for (var i = 0; i < inputsCount; ) {
        var childElement = inputs[i];
        var childElementType = childElement.getAttribute('type').toLowerCase();
        if (childElementType != 'button' && childElementType != 'submit' && childElementType != 'reset') {
            childElement.value = '';
        }
        i++;
    }

    var selects = parentEl.getElementsByTagName('select');
    var selectsCount = selects.length;
    for (var i = 0; i < selectsCount; ) {
        var childElement = selects[i];
        childElement.selectedIndex = 0;
        i++;
    }

    var textareas = parentEl.getElementsByTagName('textarea');
    var textareasCount = textareas.length;
    for (var i = 0; i < textareasCount; ) {
        var childElement = textareas[i];
        childElement.outputtext.value = '';
        i++;
    }
}

function getElementByAttr(attr_name, attr_value)
{
	var els = document.getElementsByTagName('*');
	var elsCount = els.length;
	for (var i=0;i<elsCount;)
	{
		var elem = els[i];
		if (elem.getAttribute(attr_name) == attr_value)
		{
			return elem;
			return false;
		}
		i++;
	}
}

function FocusAndClick(elID) {
    el(elID).focus();
    el(elID).click();
}

function showImages(imagesArr)
{
	//alert(imagesArr);
	var imgHTML = '';
	//alert(imagesArr.length);
	if (imagesArr.length == 0 || (imagesArr.length == 1 && imagesArr[0] == ''))
	{
		el('images').innerHTML = '';
		el('hdnImages').value = '';
		return false;
	}
	for (var i=0;i<imagesArr.length;)
	{
		//imgHTML += '<a href="'+imagesArr[i]+'" class="shutterset" ><img  src="'+imagesArr[i]+'" width="80px" height="80px" /></a> ';
		imgHTML += '<img border="0" src="'+imagesArr[i]+'" width="80px" height="80px" /> ';
		if (i>0 && i % 4 == 0)
		{
			imgHTML += '<br/>';
		}
		i++;
	}
	el('images').innerHTML = imgHTML;
	el('hdnImages').value = imagesArr;	
}

/***********************************************
* Textarea Maxlength script- © Dynamic Drive (www.dynamicdrive.com)
* This notice must stay intact for legal use.
* Visit http://www.dynamicdrive.com/ for full source code
***********************************************/

function ismaxlength(obj)
{
	var mlength=obj.getAttribute? parseInt(obj.getAttribute("maxlength")) : "";
	if (obj.getAttribute && obj.value.length>mlength)
	{
		obj.value=obj.value.substring(0,mlength);
	}
}

function SelectAll(id)
{
	 el(id).focus();
	 el(id).select();
	 return false;
}

function write(m)
{
	document.write(m);
}

function ShowMessage(msg)
{
    return '<table cellpadding="0" cellspacing="0" border="0" width="100%;-webkit-border-radius: 5px;-moz-border-radius: 5px; border-radius: 5px;"><tr><td align="center" width="90%" bgcolor="#F0E68C" style="font-size:12px;-webkit-border-radius: 5px;-moz-border-radius: 5px; border-radius: 5px;"><strong>' + msg + '</strong></td></tr></table>';
}

function setAttributeOnload(object, attribute, val) 
{
    if(window.addEventListener) {
    window.addEventListener("load",
        function(){ object[attribute] = val; }, false);
    } else {
    window.attachEvent('onload', function(){ object[attribute] = val; });
    }
}


function SaveFile(filePath, data) 
{
	try 
	{
		if (isIE)
		{
			var fso, s;
			fso = new ActiveXObject('Scripting.FileSystemObject');
			s = fso.CreateTextFile(filePath);
			s.writeline(data);
			s.Close();
		}
		else if (isNetscape)
		{
			SaveFileFF(filePath, data);
		}
	}
	catch(err)
	{
		alert(err.message);
		//document.write(err.message);
	}
}


// -------------------------------------------------------------------------------------------------
var minutes = 0;
function RefreshCountDown()
{
	try
	{
		if (window.top.min != null && window.top.sec != null)
		{
			window.top.document.getElementById('timer').innerHTML='';
			window.top.min = minutes;
			window.top.sec = 0;
			window.clearTimeout(window.top.counterTimeout);
			window.top.countDown();
		}
	}
	catch(e)
	{
		//
	}
}
 
 function DisableEnableLinks(xHow)
 {
	return ;
  objLinks = document.links;
  for(i=0;i<objLinks.length;i++){
    objLinks[i].disabled = xHow;
    //link with onclick
    if(objLinks[i].onclick && xHow){  
        objLinks[i].onclick = new Function("return false;" + objLinks[i].onclick.toString().getFuncBody());
    }
    //link without onclick
    else if(xHow){  
      objLinks[i].onclick = function(){return false;}
    }
    //remove return false with link without onclick
    else if(!xHow && objLinks[i].onclick.toString().indexOf("function(){return false;}") != -1){            
      objLinks[i].onclick = null;
    }
    //remove return false link with onclick
    else if(!xHow && objLinks[i].onclick.toString().indexOf("return false;") != -1){  
      strClick = objLinks[i].onclick.toString().getFuncBody().replace("return false;","")
      objLinks[i].onclick = new Function(strClick);
    }
  }
}

String.prototype.getFuncBody = function(){ 
  var str=this.toString(); 
  str=str.replace(/[^{]+{/,"");
  str=str.substring(0,str.length-1);   
  str = str.replace(/\n/gi,"");
  if(!str.match(/\(.*\)/gi))str += ")";
  return str; 
} 

function ValidateText4Xml(myfield, e)
{
	var key;
	var keychar;

	if (window.event)
	{
		key = window.event.keyCode;
	}
	else if (e)
	{
		key = e.which;
	}
	else
	{
		return true;
	}
	
	keychar = String.fromCharCode(key);

	// control keys
	if ((key==null) || (key==0) || (key==8) || (key==9) || (key==13) || (key==27) )
	{
		return false;
	}
	// numbers
	else if (((",\"<>").indexOf(keychar) > -1))
	{
		return false;
	}
	else
	{
		return true;
	}
}

function DecimalsOnly(myfield, e, dec)
{
	var key;
	var keychar;

	if (window.event)
	{
		key = window.event.keyCode;
	}
	else if (e)
	{
		key = e.which;
	}
	else
	{
		return true;
	}
	
	keychar = String.fromCharCode(key);

	// control keys
	if ((key==null) || (key==0) || (key==8) || (key==9) || (key==13) || (key==27) )
	{
		return true;
	}
	// numbers
	else if ((("0123456789,").indexOf(keychar) > -1))
	{
		return true;
	}
	// decimal point jump
	/*else if (dec && (keychar == ","))
	{
		myfield.form.elements[dec].focus();
		return false;
	}*/
	else
	{
		return false;
	}
}

function IntegersOnly(myfield, e)
{
	var key;
	var keychar;

	if (window.event)
	{
		key = window.event.keyCode;
	}
	else if (e)
	{
		key = e.which;
	}
	else
	{
		return true;
	}
	
	keychar = String.fromCharCode(key);

	// control keys
	if ((key==null) || (key==0) || (key==8) || (key==9) || (key==13) || (key==27) )
	{
		return true;
	}
	// numbers
	else if ((("0123456789").indexOf(keychar) > -1))
	{
		return true;
	}
	else
	{
		return false;
	}
}

function HandlePagingLinks(currentPage, pageCount, prevPageLinkID, nextPageLinkID, firstPageLinkID, lastPageLinkID)
{
	if (el(prevPageLinkID) == null || el(nextPageLinkID) == null ||
		el(firstPageLinkID) == null || el(lastPageLinkID) == null)
	{
		return false;
	}
	
	if (currentPage == 1)
	{
		el(firstPageLinkID).style.visibility = 'hidden';
		el(prevPageLinkID).style.visibility = 'hidden';
	}
	if (currentPage == pageCount)
	{	
		el(nextPageLinkID).style.visibility = 'hidden';
		el(lastPageLinkID).style.visibility = 'hidden';
	}
	
	el(firstPageLinkID).style.visibility = 'hidden';
	el(lastPageLinkID).style.visibility = 'hidden';
}

function getBrowserVersion()
{
	var b_version = navigator.appVersion;
	var version = parseFloat(b_version);
	return version;
}

var browserVersion = getBrowserVersion();

function showDialog(divId, width, height, left, top) 
{
	document.getElementById(divId).style.width = width + 'px';
	document.getElementById(divId).style.height = height + 'px';
	document.getElementById(divId).style.left = left + 'px';
	document.getElementById(divId).style.top = top + 'px';
		
	document.getElementById(divId).className = 'dimming';
	//document.getElementById(divId).style.visibility = "visible";
	document.getElementById(divId).style.display = "block";
	//Effect.toggle(divId,'slide');

	//setControlsEnability(false,'btnClose');
}

function SetPagingButtons(currentPage, pageCount)
{
	if (el('btnPreviousPage') == null || el('btnNextPage') == null)
	{
		return;
	}
	
	if (pageCount == 1)
	{
		el('btnPreviousPage').disabled = true;
		el('btnNextPage').disabled = true;
	}
	else if (currentPage == pageCount.toString())
	{
		el('btnPreviousPage').disabled = false;
		el('btnNextPage').disabled = true;
	}
	else if (currentPage == '1')
	{
		el('btnPreviousPage').disabled = true;
		el('btnNextPage').disabled = false;
	}
	else
	{
		el('btnPreviousPage').disabled = false;
		el('btnNextPage').disabled = false;
	}
}

function hideDialog(divId) 
{
	document.getElementById(divId).style.display = "none";
	//setControlsEnability(true, 'btnClose');
}

function el(id)
{
	return document.getElementById(id);
}

function getElement(id)
{
	return document.getElementById(id);
}

function SetCssClass2Elements()
{
    SetCssClass(document.body, 'input', 'button', 'button');
    SetCssClass(document.body, 'input', 'reset', 'button');
    SetCssClass(document.body, 'input', 'submit', 'button');
    SetCssClass(document.body, 'input', 'text', 'textbox');
    SetCssClass(document.body, 'input', 'password', 'textbox');
    SetCssClass2Select(document.body, 'select', 'dropdownlist');
    document.body.style.display = '';
}

function SetCssClass(parentElement, tagName, objectType, value)
{
	var items = parentElement.getElementsByTagName(tagName);
	objectType = objectType.toLowerCase();
	tagName = tagName.toLowerCase();
	var itemCount = items.length;
	if (itemCount == 0)
	{
	    return;
	}
	
	var classAttr = 'className';
	if (!isIE)
	{
	    classAttr = 'class';
	}
		
    for (i=0; i<itemCount;)
    {
		if (objectType != '' && objectType == items[i].type && 
		        (items[i].getAttribute(classAttr) == '' || 
		         items[i].getAttribute(classAttr) == 'undefined' || 
		         items[i].getAttribute(classAttr) == null)
		   )
		{
		    if (value == 'button')
		    {
		        var btnValue = items[i].getAttribute('value');
		        //if (btnValue.indexOf('<<') >= 0 || btnValue.indexOf('<') >= 0 || 
		        //    btnValue.indexOf('>') >= 0 || btnValue.indexOf('>>') >= 0 || 
		        //    btnValue.indexOf('-') >= 0)
		        if (btnValue.indexOf('<') >= 0 || btnValue.indexOf('>') >= 0)
		        {
		            value = 'buttonSmall';
		        }
		    }
		    
		    items[i].setAttribute(classAttr, value);    
		}
		i++;
    }
}

function SetCssClass2Select(parentElement, tagName, value)
{
	var items = parentElement.getElementsByTagName(tagName);
	tagName = tagName.toLowerCase();
	var itemCount = items.length;
	if (itemCount == 0)
	{
	    return;
	}
		
    for (i=0; i<itemCount;)
    {
		if (items[i].className == '')
		{
			items[i].className = value;
		}
		
		i++;
    }
}


function AttachEvent(elementObj, eventName, eventHandlerFunctionName)
{
  if (!elementObj)
  {
	return;
  }
  
  if (elementObj.addEventListener) 
  { // Non-IE browsers
    elementObj.addEventListener(eventName, eventHandlerFunctionName, false);		
  } 
  else if (elementObj.attachEvent) 
  { // IE 6+
    elementObj.attachEvent('on' + eventName, eventHandlerFunctionName);
  } 
  else 
  { // Older browsers 
    var currentEventHandler = elementObj['on' + eventName];
    if (currentEventHandler == null) 
    {
      elementObj['on' + eventName] = eventHandlerFunctionName;
    } 
    else 
    {
      elementObj['on' + eventName] = function(e) { currentEventHandler(e); eventHandlerFunctionName(e); }
    }
  }
}

function getParentElement(id)
{
	return window.parent.document.getElementById(id);
}

function RemoveLoading(sender, divLoading)
{
	//alert(sender.parent.childNodes[0].id);
	//sender.parent.removeChild(document.getElementById(divLoading));
	//sender.parent.
	if (window.parent.document.getElementById(divLoading))
	{
		window.parent.document.getElementById(divLoading).style.display = 'none';
	}
}

var openTab = null;
function LoadTab(sender, iframeID, pageName, contentdivid, preload)
{	
	if (openTab != sender)
	{
		openTab = sender;		
		
		if (contentdivid == null)
		{	
			if (el(iframeID).src != null && el(iframeID).src == '')
			{
				ShowLoader();
				el(iframeID).src = pageName;
			}
			return false;
		}
		
		if (el(contentdivid).innerHTML == '')
		{
			ShowLoader();
			//el(contentdivid).innerHTML = "Loading...";
			
			var loadingDiv = '';
			
			if (preload == true)
			{
				loadingDiv = '<div id="'+iframeID+'_divTabLoading" style="z-index:2000;font-family:verdana;font-size:12px;visibility:visible;position:absolute;left:10px;top:10px;width:200px;height:50px;BORDER-RIGHT: #FF0000 1px solid;BORDER-TOP: #FF0000 1px solid;BORDER-LEFT: #FF0000 1px solid;BORDER-BOTTOM: #FF0000 1px solid;background-color:#FFFFCC;">&nbsp;<font style="font-family:verdana;font-size:12px;color:black;"><br/>&nbsp;<img id="imgWait" src="images/loading1.gif" border="0"/>&nbsp;Παρακαλώ περιμένετε...</font><br/><br/></div>';
			}
			
			var iframeElement = loadingDiv + '<iframe id="'+iframeID+'" name="'+iframeID+'" onload="javascript:RemoveLoading(this, \''+iframeID+'_divTabLoading\');" src="about:blank" style="width:100%; height:1000px;"></iframe>';
			el(contentdivid).innerHTML = iframeElement;
			window.frames[iframeID].location.replace(pageName);
		}
				
		return true;
	}
	else
	{ 
		return false;
	}
}

function ClearTextBoxes(parentElement)
{
	if (parentElement == null)
		parentElement = document;
		
	var inputFields = parentElement.getElementsByTagName('input');
	var inpCount = inputFields.length;
	for (var i=0;i<inpCount;)
	{
		if (inputFields[i].type == 'text') 
		{
			inputFields[i].value = '';
		}
		
		i++;
	}
}

function getSelectedText(elementId) {
    var elt = document.getElementById(elementId);

    if (elt.selectedIndex == -1)
        return null;

    return elt.options[elt.selectedIndex].text;
}

function ClearSelectFields(parentElement)
{
	if (parentElement == null)
		parentElement = document;
		
	var selectFields = parentElement.getElementsByTagName('select');
	var selCount = selectFields.length;
	for (var i=0;i<selCount;)
	{
		selectFields[i].selectedIndex = 0;
		i++;
	}
}

function getSeletedIDs(selObj, delim)
{
	if (!selObj) 
	{
		alert('select object is null');
		return '-1';
	}
	
	var ids = '';
	var optCount = selObj.options.length;
	for (var i=0;i<optCount;)
	{
		if (selObj.options[i].selected)
		{
			ids += selObj.options[i].value + delim;
		}
		i++;
	}
	
	ids = CutEndingChar(ids, delim)
	
	return ids;
}

function CutStartingChar(str, ch) {
    if (str.indexOf(ch) == 0)
        str = str.substr(1, str.length-1);

    return str;
}

function CutEndingChar(str, ch)
{
	if (str.lastIndexOf(ch) > 0 && str.lastIndexOf(ch) == str.length-1) 
		str = str.substr(0, str.lastIndexOf(ch));
	
	return str;
}

function exception(e)
{
	alert('The following error occurred: \n\n' + e.name + ': '+ e.message);
}

function getBrowserName()
{
	var useragent = navigator.userAgent;
	var bName = (useragent.indexOf('Opera') > -1) ? 'Opera' : navigator.appName;
	var pos = useragent.indexOf('MSIE');
	if (pos > -1) {
	bVer = useragent.substring(pos + 5);
	var pos = bVer.indexOf(';');
	var bVer = bVer.substring(0,pos);
	}
	var pos = useragent.indexOf('Opera');
	if (pos > -1)	{
	bVer = useragent.substring(pos + 6);
	var pos = bVer.indexOf(' ');
	var bVer = bVer.substring(0, pos);
	}
	if (bName == "Netscape") {
	var bVer = useragent.substring(8);
	var pos = bVer.indexOf(' ');
	var bVer = bVer.substring(0, pos);
	}
	if (bName == "Netscape" && parseInt(navigator.appVersion) >= 5) {
	var pos = useragent.lastIndexOf('/');
	var bVer = useragent.substring(pos + 1);
	}
	
	return bName.toString();
}

//var pageInAction = false;
function OnSubmit()
{
	//pageInAction = true;
	//window.setTimeout('DisableEnableLinks(true);disableElements();ShowLoader();',1);
	window.setTimeout('ShowLoader();',1);
}

function disableElements()
{
	disableHtmlElements('input',true);
	disableHtmlElements('button',true);
	disableHtmlElements('select',true);
	disableHtmlElements('textarea',true);
	disableHtmlElements('a');
}

function enableElements()
{
	disableHtmlElements('input', false);
	disableHtmlElements('button', false);
	disableHtmlElements('select', false);
	disableHtmlElements('textarea', false);
	DisableEnableLinks(false);
	//pageInAction = false;
}

function disableHtmlElements(tag, disabled)
{
	try
	{
		var elements = document.getElementsByTagName(tag);
		var elCount = elements.length;
		if (elCount == 0)
			return;
			
		if (tag == 'input' || 
			tag == 'button' || 
			tag == 'select' || 
			tag == 'textarea')
		{
			for (var i=0;i<elCount;)
			{ 
				elements[i].disabled = disabled;
				i++;
			}
		}
		else if (isIE && browserVersion <= 6 && tag == 'select')
		{
			var visibility = 'visible';
			if (disabled)
				visibility = 'hidden';
			
			for (var i=0;i<elCount;) 
			{
				elements[i].style.visibility = visibility;
				i++;
			}
		}
		/*
		else if (tag == 'a')
		{
			for (var i=0;elements[i];i++) 
			{
				elements[i].href = '#';
				elements[i].onclick = function (){return false;};
			}
		}*/
	}
	catch(e)
	{		
	}
}

function disableChildHtmlElements(parentElement, tag, disabled)
{
	try
	{
		var elements = parentElement.getElementsByTagName(tag);
		var elCount = elements.length;
		if (elCount == 0)
			return;
			
		if (tag == 'input' || 
			tag == 'button' ||
			tag == 'textarea')
		{
			for (var i=0;i<elCount;)
			{ 
				elements[i].disabled = disabled;
				i++;
			}
		}
		else if (tag == 'select')
		{
			for (var i=0;i<elCount;)
			{
				if (isIE && majorVersion < 7)
				{
					var visibility = 'visible';
					if (disabled)
						visibility = 'hidden';
						
					elements[i].style.visibility = visibility;
				}
				else
				{
					elements[i].disabled = disabled;
				}
				
				i++;
			}
		}
		else if (tag == 'a')
		{
			for (var i=0;i<elCount;) 
			{
				elements[i].href = '#';
				elements[i].onclick = function (){return false;};
				i++;
			}
		}
	}
	catch(e)
	{		
	}
}

function displayElements(id_prefix, visibility, tag)
{
	try
	{
		//alert(parseInt(browserVersion.substring(0,1)));
		if (isIE && parseInt(browserVersion.substring(0,1)) <= 6)
		{
			var elements = document.getElementsByTagName(tag);
			var elCount = elements.length;
			if (elCount == 0)
				return;
						
			for (var i=0;i<elCount;) 
			{
				if (elements[i].id.indexOf(id_prefix) < 0)
				{
					elements[i].style.visibility = visibility;
				}
				i++;
			}
		}
	}
	catch(e)
	{		
	}
}

function removeChildNodes(element)
{
	if ( element.hasChildNodes() )
	{
		while ( element.childNodes.length >= 1 )
		{
			element.removeChild( element.firstChild );       
		} 
	}
}

var imageUrl = '';
var imageWait = null;
//var pleaseWait = '';
function ShowLoader()
{
	try
	{
		var dimmer = '<div id="divDimmer" style="filter: alpha(opacity=55); -moz-opacity: .55; background-color: #EEE;';
        dimmer += 'z-index: 900; visibility: hidden; position: absolute; left: 0px; top: 0px; width: 100%;height: 100%;"></div>';
        
        if (!el('divDimmer'))
        {
			document.body.innerHTML += dimmer;
		}
		
		el('divDimmer').style.visibility = 'visible';
        
		var verticalpos = "fromtop"
		el('loadinfo').valign = 'middle';
		el('loadinfo').style.height = '50px';
		el('loadinfo').style.width = '220px';
		el('loadinfo').style.visibility = 'visible';
		
		var startX = 10;
		var startY = 15;
		var ns = (navigator.appName.indexOf("Netscape") != -1);
		var d = document;
		function ml(id)
		{
			var elem=d.getElementById?d.getElementById(id):d.all?d.all[id]:d.layers[id];
			if(d.layers)
				elem.style = elem;
			
			elem.sP = function(x,y)
			{
				this.style.left = x;
				this.style.top = y;
			};
			
			elem.x = startX;
			if (verticalpos == 'fromtop')
			{
				elem.y = startY;
			}
			else
			{
				elem.y = ns ? pageYOffset + innerHeight : document.body.scrollTop + document.body.clientHeight;
				elem.y -= startY;
			}
			return elem;
		}
		
		window.stayTopLeft = function()
		{
			if (verticalpos == 'fromtop')
			{
				var pY = ns ? pageYOffset : document.body.scrollTop;
				ftlObj.y += (pY + startY - ftlObj.y)/8;
			}
			else
			{
				var pY = ns ? pageYOffset + innerHeight : document.body.scrollTop + document.body.clientHeight;
				ftlObj.y += (pY - startY - ftlObj.y)/8;
			}
			ftlObj.sP(ftlObj.x, ftlObj.y);
			setTimeout("stayTopLeft();", 10);
		}
		ftlObj = ml("loadinfo");
		stayTopLeft();
	}
	catch(e)
	{		
	}
}

function HideLoader()
{
	
	if (el('loadinfo'))
	{
		el('loadinfo').style.visibility = 'hidden';
		if (el('divDimmer'))
		{
			el('divDimmer').style.visibility = 'hidden';
		}
	}
	
	if (window.parent.document.getElementById('loadinfo'))
	{
		window.parent.document.getElementById('loadinfo').style.visibility = 'hidden';
		if (window.parent.document.getElementById('divDimmer'))
		{
			window.parent.document.getElementById('divDimmer').style.visibility = 'hidden';
		}
	}
	
	if (window.parent.parent.document.getElementById('loadinfo'))
	{
		window.parent.parent.document.getElementById('loadinfo').style.visibility = 'hidden';
		if (window.parent.parent.document.getElementById('divDimmer'))
		{
			window.parent.parent.document.getElementById('divDimmer').style.visibility = 'hidden';
		}
	}
	
	minutes = 20;
	RefreshCountDown();
}

function disableInputElements()
{
	try
	{
		var inputs = document.getElementsByTagName('input');
		var inputCount = inputs.length;
		if (inputCount == 0)
			return;
		
		for (var i=0;i<inputCount;)
		{ 
			inputs[i].disabled = true;
			i++;
		}
	}
	catch(e)
	{
	}
}

function disableButtonElements()
{
	try
	{
		var buttons = document.getElementsByTagName('button');
		var btnCount = buttons.length;
		if (btnCount == 0)
			return;
		
		for (var i=0;i<btnCount;) 
		{
			buttons[i].disabled = true;
			i++;
		}
	}
	catch(e)
	{		
	}
}

function disableSelectElements()
{
	try
	{
		var selects = document.getElementsByTagName('select');
		var selCount = selects.length;
		if (selCount == 0)
			return;
		
		for (var i=0;i<selCount;)
		{
			selects[i].disabled = true;
			i++;
		}
	}
	catch(e)
	{
	}
}

function disableTextAreaElements()
{
	try
	{
		var textareas = document.getElementsByTagName('textarea');
		var taCount = textareas.length;
		if (taCount == 0)
			return;
			
		for (var i=0;i<taCount;)
		{ 
			textareas[i].disabled = true;
			i++;
		}
	}
	catch(e)
	{
	}
}

function disableLinkElements()
{
	try
	{
		var links = document.getElementsByTagName('a');
		var lnkCount = links.length;
		if (lnkCount == 0)
			return;
		
		for (var i=0;i<lnkCount;) 
		{
			links[i].href = '#';
			links[i].onclick = function (){return false;};
			i++;
		}
	}
	catch(e)
	{		
	}
}

function SetAccess(accessTag, tagName)
{
	var ctls = document.getElementsByTagName(tagName);
	var ctlCount = ctls.length;
	for (var i=0;i<ctlCount;)
	{
		var itemTag = getAccessTag(ctls[i]);
		if (itemTag < accessTag)
		{
			ctls[i].style.display = 'none';
		}
		i++;
	}
}

function urlParam( name )
{
  name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
  var regexS = "[\\?&]"+name+"=([^&#]*)";
  var regex = new RegExp( regexS );
  var results = regex.exec( window.location.href );
  if( results == null )
    return '';
  else
    return results[1];
}

function CenterElement(id)
{
	if (el(id))
	{
		var elem = el(id);		
		var w, h, l, t;
		w = el(id).style.width.replace('px','');
		h = el(id).style.height.replace('px','');
		
		l = getCenterX(w);
		t = getCenterY(h);
		
		elem.style.left = l + 'px';
		elem.style.top = (t-200) + 'px';
	}
}

function GotoLoginPage(location)
{
	window.parent.location.href = location;
}

function getDropdownListSelectedText(selObj)
{
	return selObj.options[selObj.selectedIndex].text;
}

function deleteOptionByValue(selObj, value)
{
	var optCount = selObj.options.length;
	for (var i=0;i<optCount;)
	{
		if (selObj.options[i].value == value)
		{
			selObj.options[i] = null;
			//selObj.options[i].readonly = 'readonly';
			return;
		}
		i++;
	}
}

function getDropdownListSelectedValue(selObj)
{
	return selObj.options[selObj.selectedIndex].value;
}

function setDropdownListSelectedValue(selObj, value)
{
	var selectedIndex = 0;
	var optCount = selObj.options.length;
	for (var i=0;i<optCount;)
	{
		if (selObj.options[i].value == value)
		{
			selectedIndex = i;
			break;
		}
		i++;
	}
	
	selObj.selectedIndex = selectedIndex;
}

function setSelectedOption(selObj, value)
{
	var selectedIndex = -1;
	var optCount = selObj.length;
	for (var i=0;i<optCount;)
	{
		if (selObj.options[i].value == value)
		{
			selectedIndex = i;
			selObj.options[i].selected = true;
			break;
		}
		
		i++;
	}
	
	selObj.options[selectedIndex].selected = true;
}

function setSelectedOptionByText(selObj, text)
{
	var selectedIndex = -1;
	var optCount = selObj.length;
	for (var i=0;i<optCount;)
	{
		if (selObj.options[i].text == text)
		{
			selectedIndex = i;
			selObj.options[i].selected = true;
			break;
		}
		
		i++;
	}
	
	selObj.options[selectedIndex].selected = true;
}

function FixElement(id)
{
	if (el(id))
	{
		var elem = el(id);
		elem.style.left = '100px';
		elem.style.top = '100px';
	}
}

function DisableControl(controlId)
{
	el(controlId).disabled = true;
}
 
function DisableControl_SetTimeout(controlId,interval)
{
	setTimeout("DisableControl('" +controlId + "')",interval);
}

function getIFrameElement(iframeID, elementID)
{
	return document.frames(iframeID).document.getElementById(elementID);
}

function popup(url,name,width,height,scrollbars) 
{
	var sizeX = width;
	var sizeY = height;
	var winX=screen.availWidth;
	var winY=screen.availHeight;	
	var centerX=eval(winX/2-sizeX/2);
	var centerY=eval(winY/2-sizeY/2);
	var param ='scrollbars='+scrollbars+',status=yes,resizable=yes,top='+centerY+',left='+centerX+',width='+sizeX+',height='+sizeY;
	var newWin = window.open(url,name,param);
	newWin.focus();

	return false;
}

function ApplyClassAttribute2HtmlControls(parentElement, tagName, objectType, value)
{
	var items = parentElement.getElementsByTagName(tagName);
	objectType = objectType.toLowerCase();
	tagName = tagName.toLowerCase();
	var itemCount = items.length;
    for (i=0; i<itemCount;)
    {
		if (objectType != '' && objectType == items[i].type)
		{
			items[i].setAttribute('className', value);
		}
		i++;
    }
}

function ApplyAttribute2HtmlControls(tagName, objectType, attribute, value)
{		
	if (objectType == '')
		return;
		
	var theForm = document.forms(0);
	var items = theForm.length;
	objectType = objectType.toLowerCase();
	tagName = tagName.toLowerCase();
    for (i=0; i<items; )
    {
		var currentElement =  theForm.elements[i];
		if (objectType == currentElement.type)
		{
			try
			{
				if (currentElement.getAttribute(attribute).value == '')
					currentElement.setAttribute(attribute, value);
				
				//ApplyAttribute2HtmlControls(items[i], tagName, objectType, attribute, value)
			}
			catch(e)
			{
				alert(e.description);
			}
		}
		
		i++;
    }
}

function ApplyStyle2HtmlControls(parentElement, tagName, objectType, the_value)
{
	if (parentElement == null)
		return;
		
	var items = parentElement.getElementsByTagName(tagName);
	objectType = objectType.toLowerCase();
	tagName = tagName.toLowerCase();
	var itemsCount = items.length;
    for (i=0; i<itemsCount; )
    {
		if (objectType != '' && objectType == items[i].type)
		{
			try
			{
				items[i].setAttribute('style', the_value);
			}
			catch(e)
			{
				//alert(e.description);
			}
		}
		i++;
    }
}

function set_cookie(c_name, value, expiredays)
{
	var exdate=new Date();
	exdate.setDate(exdate.getDate()+expiredays);
	document.cookie=c_name+ "=" +escape(value)+
	((expiredays==null) ? "" : ";expires="+exdate.toGMTString());
}

function set_cookie(variable, value)
{
	document.cookie = variable + '=' + value;
}

function get_cookie(Name) 
{
	var search = Name + "="
	var returnvalue = '';
	if (document.cookie.length > 0) 
	{
		offset = document.cookie.indexOf(search);
		// if cookie exists
		if (offset != -1) 
		{
			offset += search.length
			// set index of beginning of value
			end = document.cookie.indexOf(';', offset);
			
			// set index of end of cookie value
			if (end == -1) 
				end = document.cookie.length;
		
			returnvalue=unescape(document.cookie.substring(offset, end));
		}
	}
	return returnvalue;
}

var TRange = null

function findString (str) {
 if (parseInt(navigator.appVersion)<4) return;
 var strFound;
 if (navigator.appName=="Netscape") {

  // NAVIGATOR-SPECIFIC CODE

  strFound=self.find(str);
  if (!strFound) {
   strFound=self.find(str,0,1)
   while (self.find(str,0,1)) continue
  }
 }
 if (navigator.appName.indexOf("Microsoft")!=-1) {

  // EXPLORER-SPECIFIC CODE

  if (TRange!=null) {
   TRange.collapse(false)
   strFound=TRange.findText(str)
   if (strFound) TRange.select()
  }
  if (TRange==null || strFound==0) {
   TRange=self.document.body.createTextRange()
   strFound=TRange.findText(str)
   if (strFound) TRange.select()
  }
 }
 if (!strFound) alert ("String '" + str + "' not found!")
}

function CheckUndefined(value, element_type)
{
	if (value != 'undefined')
	{
		return value;
	}
	else if (value == '' || value == 'undefined')
	{
		if (element_type == 'textbox')
		{
			return '';
		}
		else if (element_type == 'select')
		{
			return '-1';
		}
	}
}

/*	CleanForDataBase	*/
function CleanForDataBase( strTextToClean )
{
	if ( strTextToClean != null && strTextToClean != 'undefined' && strTextToClean != '' )
	{
		strTextToClean = strTextToClean.replace("&", "%26");
		strTextToClean = strTextToClean.replace("#", " ");
//		strTextToClean = strTextToClean.replace("&", " ");
		strTextToClean = strTextToClean.replace("'", " ");
		strTextToClean = strTextToClean.replace("\"", " ");
//		strTextToClean = strTextToClean.replace("?", " ");
//		strTextToClean = strTextToClean.replace("=", " ");
//		strTextToClean = strTextToClean.replace("|", " ");
//		strTextToClean = strTextToClean.replace("~", " ");
		strTextToClean = strTextToClean.replace("#{@@}#", " ");
//		strTextToClean = strTextToClean.replace("*", " ");

		strTextToClean = strTextToClean.replace("\n", " ");
		strTextToClean = strTextToClean.replace("\t"," ");
	}

	return strTextToClean ;
}

function clearElements(parentElement, tagName, objectType)
{
	var items = parentElement.getElementsByTagName(tagName);
	objectType = objectType.toLowerCase();
	tagName = tagName.toLowerCase();
	var itemsCount = items.length;
    for (i=0; i<itemsCount; )
    {
		if (objectType != '')
		{
			if (items[i].type != 'button' && items[i].type != 'submit')
			{
				if (objectType == 'text' || objectType == 'hidden')
				{
					items[i].value = '';
				}	
			}
		}			
		else
		{
			if (tagName == 'select')
			{
				items[i].selectedIndex = 0;
			}
		}
		
		i++;
    }
}

function getCenterX(width)
{	
	var winX = screen.availWidth;
	return eval(winX/2-width/2);
}

function getCenterY(height)
{
	var winY = screen.availHeight;	
	return eval(winY/2-height/2);
}

function centerElement(elem)
{
    var sizeX = elem.offsetWidth;
    var sizeY = elem.offsetHeight;
	var winX = screen.availWidth;
	var winY = screen.availHeight;	
	var centerX = eval(winX/2-sizeX/2);
	var centerY = eval(winY/2-sizeY/2);
	elem.style.left = centerX;
	elem.style.top =  centerY;
}

function setElementCoords(el, left, top)
{
	el.style.left = left + 'px';
	el.style.top =  top + 'px';
}

function findPosX(obj)
{
	var curleft = 0;
	if(obj.offsetParent)
		while(1)
		{
			curleft += obj.offsetLeft;
			if(!obj.offsetParent)
			break;
			obj = obj.offsetParent;
		}
	else if(obj.x)
		curleft += obj.x;
	return curleft;
}

function findPosY(obj)
{
	var curtop = 0;
	if(obj.offsetParent)
		while(1)
		{
			curtop += obj.offsetTop;
			if(!obj.offsetParent)
			break;
			obj = obj.offsetParent;
		}
	else if(obj.y)
		curtop += obj.y;
	return curtop;
}

function findPos(obj) {
    var curleft = curtop = 0;
    if (obj && obj.offsetParent) {
        do {
            curleft += obj.offsetLeft;
            curtop += obj.offsetTop;
        } while (obj = obj.offsetParent);
    }
    return [curleft, curtop];
}

function CalendarSetDate(calID, day, month, year)
{
	el(calID + "_selDay").value = day;
	el(calID + "_selMonth").value = month;
	el(calID + "_selYear").value = year;
}

function ClearValidators()
{
	//for (var i=0;i<el("theForm").length;i++)
	var frmCount = document.forms[0].length;
	for (var i=0;i<frmCount;)
	{
		var spanElement = document.getElementsByTagName("span").item(i);
		if (spanElement != null && spanElement.id.indexOf("_Validator") >= 0)
		{
			spanElement.style.visibility = "hidden";
		}
			
		i++;
	}
}

function y2k(number)
{
	return (number < 1000) ? number + 1900 : number;
}

function isDate (day, month, year) {
// checks if date passed is valid
// will accept dates in following format:
// isDate(dd,mm,ccyy), or
// isDate(dd,mm) - which defaults to the current year, or
// isDate(dd) - which defaults to the current month and year.
// Note, if passed the month must be between 1 and 12, and the
// year in ccyy format.

    var today = new Date();
    year = ((!year) ? y2k(today.getYear()):year);
    month = ((!month) ? today.getMonth():month-1);
    if (!day) return false
    var test = new Date(year,month,day);
    if ( (y2k(test.getYear()) == year) &&
         (month == test.getMonth()) &&
         (day == test.getDate()) )
        return true;
    else
        return false
}

function ConvertDate4Comparison(theDate)
{
	var d = theDate.split('/');
	return d[1] + '/' + d[0] + '/' + d[2];
}

function CompareDates(date1, date2)
{
	if (Date.parse(date1) == Date.parse(date2)) 
		return 0;
	else if (Date.parse(date1) > Date.parse(date2)) 
		return 1;
	else if (Date.parse(date1) < Date.parse(date2)) 
		return -1;
	else 
		return null;
}

function HighLightSelectedItems()
{	
	try
	{
		if (el('lbSelectedItems') == null)
			return false;
			
		var optCount = el('lbSelectedItems').options.length;
			
		for (j=0;j<optCount;)
		{
			el(el('lbSelectedItems').options[j].value).style.backgroundColor = 'silver';
			j++;
		}
	}	
	catch(e)
	{
		alert('function HighLightSelectedItems exception: ' + e.message);
		return false;
	}
	return true;
}

function HighLightSelectedItems(elem1, elem2)
{	
	try
	{
		if (!elem1 || !elem2)
			return false;
					
		var optCount = elem1.options.length;
			
		for (j=0;j<optCount;)
		{
			var value = elem1.options[j].value;
			if (optionValueIndexOf(elem2.options, value) >= 0)
			{
				elem1.options[j].style.backgroundColor = 'silver';
			}
			j++;
		}
	}	
	catch(e)
	{
		alert('function HighLightSelectedItems(elem1, elem2) exception: ' + e.message);
		return false;
	}
	return true;
}

function optionValueIndexOf(options,value) 
{
	for (var i=0;i<options.length;) 
	{
		if (options[i].value == value) 
		{
			return i;
		}
		i++;
	}
	
	return -1;
}

function LoadJavascriptFile(filename, appendElementTag)
{
	var fileref=document.createElement('script');
	fileref.setAttribute("type","text/javascript");
	fileref.setAttribute("src", filename);
	if (typeof fileref != "undefined")
		document.getElementsByTagName(appendElementTag)[0].appendChild(fileref);
}

function LoadCssFile(filename)
{
	var fileref=document.createElement("link");
	fileref.setAttribute("rel", "stylesheet");
	fileref.setAttribute("type", "text/css");
	fileref.setAttribute("href", filename);

	if (typeof fileref != "undefined")
		document.getElementsByTagName('head')[0].appendChild(fileref);
}


var NS4 = (navigator.appName == "Netscape" && parseInt(navigator.appVersion) < 5);

function OptionExists(elem, text, value)
{
	var optCount = elem.length;
	for (var i=0;i<optCount;)
	{
		if (elem.options[i].value == value && elem.options[i].text == text)
		{
			return true;
		}
		
		i++;
	}
	
	return false;
}

function addOption(theSel, theText, theValue)
{
  var newOpt = new Option(theText, theValue);
  var selLength = 0;
  try
  {
	selLength = theSel.length;
  }
  catch(e)
  {
	alert(e.message);
  }
  
  if (!OptionExists(theSel, theText, theValue))
  {
	theSel.options[selLength] = newOpt;
  }
}

function deleteOption(theSel, theIndex)
{
  var selLength = theSel.length;
  if(selLength>0)
  {
    theSel.options[theIndex] = null;
  }
}

function deleteOptions(theSel)
{
  var selLength = theSel.length;
  if(selLength>0)
  {
    for (var i=selLength-1;i>=0;i--)
	{
		theSel.options[i] = null;
	}
  }
}


function selectOption(elem, value)
{
	var optCount = elem.length;
	for (var i=0;i<optCount;)
	{
		if (elem.options[i].value == value)
		{
			elem.options[i].selected = true;
			return true;
		}
		
		i++;
	}
	
	return false;
}

function getOption(elem, value)
{
	var optCount = elem.length;
	for (var i=0;i<optCount;)
	{
		if (elem.options[i].value == value)
		{
			return false;
		}
		
		i++;
	}
	
	return true;
}

function copyOptions(theSelFrom, theSelTo)
{
  var selLength = theSelFrom.length;
  var selectedText = new Array();
  var selectedValues = new Array();
  var selectedCount = 0;

  var i;

  // Find the selected Options in reverse order
  // and delete them from the 'from' Select.
  for(i=selLength-1; i>=0;)
  {
    
    selectedText[selectedCount] = theSelFrom.options[i].text;
    selectedValues[selectedCount] = theSelFrom.options[i].value;
    selectedCount++;
    i--;
  }

  for(i=selectedCount-1; i>=0; )
  {
    addOption(theSelTo, selectedText[i], selectedValues[i]);
    i--;
  }

  if(NS4) history.go(0);
}

function moveSelectedOptions(theSelFrom, theSelTo)
{
  var selLength = theSelFrom.length;
  var selectedText = new Array();
  var selectedValues = new Array();
  var selectedCount = 0;

  var i;

  // Find the selected Options in reverse order
  // and delete them from the 'from' Select.
  for(i=selLength-1; i>=0;)
  {
    if(theSelFrom.options[i].selected)
    {
      selectedText[selectedCount] = theSelFrom.options[i].text;
      selectedValues[selectedCount] = theSelFrom.options[i].value;
      //deleteOption(theSelFrom, i);
      selectedCount++;
    }
    
    i--;
  }

  // Add the selected text/values in reverse order.
  // This will add the Options to the 'to' Select
  // in the same order as they were in the 'from' Select.
  for(i=selectedCount-1; i>=0; )
  {
    addOption(theSelTo, selectedText[i], selectedValues[i]);
    i--;
  }

  if(NS4) history.go(0);
}

function deleteSelectedOptions(theSel)
{
  var selLength = theSel.length;
  var selectedText = new Array();
  var selectedValues = new Array();
  var selectedCount = 0;

  var i;

  // Find the selected Options in reverse order
  // and delete them from the 'from' Select.
  for(i=selLength-1; i>=0; )
  {
    if(theSel.options[i].selected)
    {
      deleteOption(theSel, i);
    }
    i--;
  }

  if(NS4) history.go(0);
}

function selectMultipleOptions_all(select_element, selected)
{
	var selObj = select_element;
	var optCount = selObj.length;
	for (i=0;i<optCount;)
	{
		selObj.options[i].selected = selected;
		i++;
	}
}

function sortSelectElement(selectElement)
{
	var lb = selectElement;
	arrTexts = new Array();
	
	var optCount = lb.length;

	for(i=0; i<optCount; )
	{
	  arrTexts[i] = lb.options[i].text + "$" + lb.options[i].value;
	  i++;
	}

	arrTexts.sort();

	for(i=0; i<optCount; )
	{
		var option =  arrTexts[i].split("$")
		var text = option[0];
		var value = option [1];
	    lb.options[i].text = text;
	    lb.options[i].value = value;
	    i++;
	}
}

function moveOptions(theSelFrom, theSelTo)
{
  var selLength = theSelFrom.length;
  var selectedText = new Array();
  var selectedValues = new Array();
  var selectedCount = 0;

  var i;

  // Find the selected Options in reverse order
  // and delete them from the 'from' Select.
  for(i=selLength-1; i>=0; )
  {
    //if(theSelFrom.options[i].selected)
    //{
      selectedText[selectedCount] = theSelFrom.options[i].text;
      selectedValues[selectedCount] = theSelFrom.options[i].value;
      //deleteOption(theSelFrom, i);
      selectedCount++;
    //}
    i--;
  }

  // Add the selected text/values in reverse order.
  // This will add the Options to the 'to' Select
  // in the same order as they were in the 'from' Select.
  for(i=selectedCount-1; i>=0; )
  {
    addOption(theSelTo, selectedText[i], selectedValues[i]);
    i--;
  }

  if(NS4) history.go(0);
}

/*function FillSelectHtmlControl(selectId, valuesArray, textsArray)
{
	for (i=0;i<valuesArray.length;i++)
	{
		el(selectId).options[i] = new Option(valuesArray[i], textsArray[i], false);
	}
}*/

function FillSelectHtmlControl1(selectId, optionsArray, firstOption)
{
	el(selectId).options[0] = new Option(firstOption, '-1' , false);
	for (i=0;i<optionsArray.length;i++)
	{
		var option = optionsArray[i];
		var text = option.split('#')[0];
		var value = option.split('#')[1];
		
		el(selectId).options[i+1] = new Option(value, text, false);
	}
}

function FillSelectHtmlControl(selectId, optionsArray, firstOption)
{
	el(selectId).options[0] = new Option(firstOption, '-1' , false);
	for (i=0;i<optionsArray.length;i++)
	{
		var option = optionsArray[i];
		var text = option;
		var value = option;
		
		el(selectId).options[i+1] = new Option(value, text, false);
	}
}

function FillDaysSelect(selectId, optionsArray, firstOption)
{
	el(selectId).options[0] = new Option(firstOption, '-1' , false);
	for (i=0;i<optionsArray.length;i++)
	{
		var option = optionsArray[i];
		var text = option;
		var value = option;
		
		el(selectId).options[i+1] = new Option(text, i.toString(), false);
	}
}

function FillHoursSelect(selectId)
{
	for (i=0;i<24;i++)
	{
		var hour = i.toString();
		if (i<10) hour = '0' + i.toString();
		el(selectId).options[i] = new Option(hour, i, false);
	}
	el(selectId).selectedIndex = 0;
}

function FillMinsSelect(selectId)
{
	var optionIndex = 0;
	for (i=0;i<59;i+=5)
	{
		var min = i.toString();
		if (i<10) min = '0' + i.toString();
		el(selectId).options[optionIndex] = new Option(min, i, false);
		optionIndex++;
	}
	el(selectId).selectedIndex = 0;
}

function FillSelectHtmlControl(selectId, optionsArray, firstOption)
{
	el(selectId).options[0] = new Option(firstOption, '-1' , false);
	for (i=0;i<optionsArray.length;i++)
	{
		var option = optionsArray[i];
		var text = option;
		var value = option;
		
		el(selectId).options[i+1] = new Option(value, text, false);
	}
}

function ClearSelectHtmlControl(selectId)
{
	for (i=el(selectId).options.length-1;i>=0;i--)
	{		
		el(selectId).options[i] = null;
	}
}

function FillSelectHtmlControlWithStream(selectId, optionsStream)
{
	ClearSelectHtmlControl(selectId);
	if (optionsStream == '')
		return;
	
	var arr = optionsStream.split(",");
	for (i=0;i<arr.length;i++)
	{
		var option = arr[i];
		var optionArray = option.split("#");
		
		el(selectId).options[i] = new Option(optionArray[0], optionArray[1], false);
	}
}

function getOptionsArray(elemID)
{
	var element = el(elemID);
	var optionsArray = Array();
	var optCount = element.options.length;
	for(i=0;i<optCount;)
	{
		optionsArray[i] = element.options[i].text + '#' + element.options[i].value;
		i++;
	}
	
	return optionsArray;
}

function addEvent(obj, evType, fn)
{ 
	if (obj.addEventListener)
	{ 
		obj.addEventListener(evType, fn, false); 
		return true; 
	} 
	else if (obj.attachEvent)
	{ 
		var r = obj.attachEvent("on"+evType, fn); 
		return r; 
	} 
	else 
	{ 
		return false; 
	} 
}

function DDLSelection(elem)
{
	alert(elem.selectedIndex);
	if (elem.selectedIndex == 0)
		return false;
	
	return true;	
}

function ValidateEmail(email) 
{
	return (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,7})+$/.test(email))
}

function ValidatePagingNav(total_rows, page_size)
{
	return (total_rows == page_size);
}

/*
function OnEnterKeyPressed(targetElementPostbackID) 
{
	if (window.event && window.event.keyCode == 13)
	{
		try
		{
			
		}
		catch (e)
		{
			alert(e.message);
		}
	}
}
*/

function enter_key_trap(event)
{
    var key;
    if (event.keyCode) {
        key = event.keyCode;
    } else if (event.which) {
        key = event.which;
    } else {
        return false;
    }

    return (key == 10 || key == 13);
}

function OnEnterKeyPressed(e, element)
{
	if (window.event) { e = window.event; }
	if (e.keyCode == 13) {

	    element.focus();
	    element.click();
	    return true;
	}
}

function EnterKeyPressed()
{
	if (window.event && window.event.keyCode == 13)
	{
		return true;
	}
	
	return false;
}

/*
function OnEnterKeyPressed(elementID) 
{
	if (window.event && window.event.keyCode == 13)
	{
		try
		{
			el(elementID).click();
		}
		catch (e)
		{
			alert(e.message);
		}
	}
}*/

// functions for manipulating list checkboxes

function getChecked()
{
	var itemsChecked = 0;
	for (i=0;i<itemsCount;)
	{
		if (el('chk_'+i) == null)
		{
			return 0;
		}		
		if (el('chk_'+i).checked)
		{
			itemsChecked++
		}
		i++;
	}
	
	return itemsChecked;
}

function CheckAll(elem)
{
	for (i=0;i<itemsCount;)
	{
		if (el('chk_'+i))
		{
			if (el('chk_'+i).style.display != 'none')
			{
				el('chk_'+i).checked = elem.checked;
			}
		}
		i++;
	}
}

function chkItemClicked(elem)
{
	var allChecked = true;
	
	for (i=0;i<itemsCount;)
	{
		if (el('chk_'+i))
		{
			if (!el('chk_'+i).checked)
			{
				allChecked = false;
				break;
			}
		}
		i++;
	}
	
	el('chkAll').checked = allChecked;
	
	/*
	if (el.checked)
	{
		var id = el.id.replace('chk_','tr_')
		
		el(id).style.bgcolor = '#0000ff';
		alert(el(id).innerHTML);
		//this.parent.parent.style.bgcolor='blue';
	}*/
}

function setSelectControls(visibility)
{
	var selObjs = document.getElementsByTagName('select');
	var selObjCount = selObjs.length;
	for (var i=0;i<selObjCount;)
	{
		var selCtl = document.getElementsByTagName('select')[i];
		if (selCtl.id != 'ddlDistrict' &&  selCtl.id != 'ddlCountry')
		{
			selCtl.style.visibility = visibility;
		}
			
		i++;
	}

	//el('lbIntlUsers1').style.visibility = visibility;
}

function dimmerDiv(visibility)
{
	document.getElementById('dimmer').style.width = document.body.clientWidth + 'px';
	document.getElementById('dimmer').style.height = document.body.clientHeight + 'px';
	document.getElementById('dimmer').style.visibility = visibility;
}

function HighLightListRows(list)
{
	if (list)
	{
		var trs = list.getElementsByTagName('tr');
		var trCount = trs.length;
		for (var i=0;i<trCount;)
		{
			if (i > 0 && i < 16)
			{
				trs[i].onmouseover = function () { if (el('chk_'+(i-1).toString())) {if (!el('chk_'+(i-1).toString()).checked){ HighlightRow(this, true);}} };
				trs[i].onmouseout = function () { if (el('chk_'+(i-1).toString())) { if (!el('chk_'+(i-1).toString()).checked){ HighlightRow(this, false);}} };
			}
			i++;
		}
	}
}


var nVer = navigator.appVersion;
var nAgt = navigator.userAgent;
var browserName  = '';
var fullVersion  = 0; 
var majorVersion = 0;

// In Internet Explorer, the true version is after "MSIE" in userAgent
if ((verOffset=nAgt.indexOf("MSIE"))!=-1) {
 browserName  = "Microsoft Internet Explorer";
 fullVersion  = parseFloat(nAgt.substring(verOffset+5));
 majorVersion = parseInt(''+fullVersion);
}

// In Opera, the true version is after "Opera" 
else if ((verOffset=nAgt.indexOf("Opera"))!=-1) {
 browserName  = "Opera";
 fullVersion  = parseFloat(nAgt.substring(verOffset+6));
 majorVersion = parseInt(''+fullVersion);
}

// In Firefox, the true version is after "Firefox" 
else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) {
 browserName  = "Firefox";
 fullVersion  = parseFloat(nAgt.substring(verOffset+8));
 majorVersion = parseInt(''+fullVersion);
}

// In most other browsers, "name/version" is at the end of userAgent 
else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) < (verOffset=nAgt.lastIndexOf('/')) ) 
{
 browserName  = nAgt.substring(nameOffset,verOffset);
 fullVersion  = parseFloat(nAgt.substring(verOffset+1));
 if (!isNaN(fullVersion)) majorVersion = parseInt(''+fullVersion);
 else {fullVersion  = 0; majorVersion = 0;}
}

// Finally, if no name and/or no version detected from userAgent...
if (browserName.toLowerCase() == browserName.toUpperCase()
 || fullVersion==0 || majorVersion == 0 )
{
 browserName  = navigator.appName;
 fullVersion  = parseFloat(nVer);
 majorVersion = parseInt(nVer);
}
/*

document.write('Browser name  = '+browserName+'<br>');
document.write('Full version  = '+fullVersion+'<br>');
document.write('Major version = '+majorVersion+'<br>');
document.write('navigator.appName = '+navigator.appName+'<br>');
document.write('navigator.userAgent = '+navigator.userAgent+'<br>');
*/


