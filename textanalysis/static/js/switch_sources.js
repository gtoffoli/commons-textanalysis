function remoteCssLoaded () {
/*
  // document.styleSheets holds the style sheets from LINK and STYLE elements
  for (var i = 0; i < document.styleSheets.length; i++) {

    // Checking if there is a request for the css file
    // We iterate the style sheets with href attribute that are created from LINK elements
    // STYLE elements don't have href attribute, so we ignore them
    // We also check if the href contains the css file name
    if (document.styleSheets[i].href && document.styleSheets[i].href.match("/template.css")) {

        console.log("There is a request for the css file.");

        // Checking if the request is unsuccessful
        // There is a request for the css file, but is it loaded?
        // If it is, the length of styleSheets.cssRules should be greater than 0
        // styleSheets.cssRules contains all of the rules in the css file
        // E.g. b { color: red; } that's a rule
        if (document.styleSheets[i].cssRules.length == 0) {

            // There is no rule in styleSheets.cssRules, this suggests two things
            // Either the browser couldn't load the css file, that the request failed
            // or the css file is empty. Browser might have loaded the css file,
            // but if it's empty, .cssRules will be empty. I couldn't find a way to
            // detect if the request for the css file failed or if the css file is empty

            console.log("Request for the css file failed.");

            // There is a request for the css file, but it failed. Fallback
            // We don't need to check other sheets, so we break;
            break;
        } else {
            // If styleSheets.cssRules.length is not 0 (>0), this means 
            // rules from css file is loaded and the request is successful
            console.log("Request for the css file is successful.");
            break;
        }
    }
    // If there isn't a request for the css file, we fallback
    // But only when the iteration is done
    // Because we don't want to apply the fallback at each iteration
    else if (i == document.styleSheets.length - 1) {
        // Fallback
        console.log("There is no request for the css file.");
    }
  }
*/
	var remote_ids = [];
	elements = document.getElementsByTagName("link");
    for (var i = 0; i < elements.length; i++) {
		var id = elements[i].id;
		if (id)
			remote_ids.push(id);
	}
	return remote_ids;
}
function remoteJsLoaded() {
	var remote_ids = [];
	elements = document.getElementsByTagName("script");
    for (var i = 0; i < elements.length; i++) {
		var id = elements[i].id;
		if (id)
			remote_ids.push(id);
	}
	return remote_ids;
}