// Google Map
var map;

// markers for map
var markers = [];

// info window
var info = new google.maps.InfoWindow();

// execute when the DOM is fully loaded
$(function() {

    // styles for map
    // https://developers.google.com/maps/documentation/javascript/styling
    var styles = [

        // hide Google's labels
        {
            featureType: "all",
            elementType: "labels",
            stylers: [
                {visibility: "off"}
            ]
        },

        // hide roads
        {
            featureType: "road",
            elementType: "geometry",
            stylers: [
                {visibility: "off"}
            ]
        }
    ];

    // options for map
    // https://developers.google.com/maps/documentation/javascript/reference#MapOptions
    var options = {
        center: {lat: 39.1157, lng: -94.6271}, // Kansas City, KS
        disableDefaultUI: true,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        maxZoom: 14,
        panControl: true,
        styles: styles,
        zoom: 5,
        zoomControl: true
    };

    // get DOM node in which map will be instantiated
    var canvas = $("#map-canvas").get(0);

    // instantiate map
    map = new google.maps.Map(canvas, options);

    // configure UI once Google Map is idle (i.e., loaded)
    google.maps.event.addListenerOnce(map, "idle", configure);
    
});

/**
 * Adds marker for place to map.
 */
function addMarker(place)
{
    // map icon settings
    var pin = {url:"https://maps.google.com/mapfiles/kml/pal2/icon14.png",
            size: new google.maps.Size(80, 80),
            origin: new google.maps.Point(-25, 0),
            anchor: new google.maps.Point(0, 0),
            scaledSize: new google.maps.Size(25, 25)
    };
    // create and position marker
    var myLabel =  place.place_name + ", " + place.admin_code1;
    var myLatLng = {lat: parseFloat(place.latitude), lng: parseFloat(place.longitude)};
    // new marker object...
    var marker = new google.maps.Marker({
        position: myLatLng,
        icon: pin,
        title: place.place_name,
        label: myLabel
    });
    
    marker.setMap(map);
    
    markers.push(marker);
    
    // create event call for info list....
    marker.addListener('click', function(){
    
        var parameters = {
            geo: place.postal_code
        };
        
        // request JSON from Lookup ...through articles...call showInfo function....
        $.getJSON(Flask.url_for("articles"), parameters)
        .done(function(data, textStatus, jqXHR){
            showInfo(marker, data);
        })
        .fail(function(jqXHR, textStatus, errorThrown){
            console.log(errorThrown.toString());
        });
    });
}

/**
 * Configures application.
 */
function configure()
{
    // update UI after map has been dragged
    google.maps.event.addListener(map, "dragend", function() {

        // if info window isn't open
        // http://stackoverflow.com/a/12410385
        if (!info.getMap || !info.getMap())
        {
            update();
        }
    });

    //update UI after zoom level changes
    google.maps.event.addListener(map, "zoom_changed", function() {
        if (!info.getMap || !info.getMap())
        {
            update();
        }
    });
    

    // configure typeahead
    $("#q").typeahead({
        highlight: false,
        minLength: 1
    },
    {
        display: function(suggestion) { return null; },
        limit: 10,
        source: search,
        templates: {
            suggestion: Handlebars.compile(
                "<div>" +
                "{{place_name}}, {{admin_name1}}, {{postal_code}}" +
                "</div>"
            )
        }
    });

    // re-center map after place is selected from drop-down
    $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {

        // set map's center
        /* possible future animation....
        home_wide = {lat: 39.1157, lng: -94.6271}; // K.C., KS
        map.panTo(home_wide);
        map.setZoom(5);
        */
        //map.setCenter({lat: parseFloat(suggestion.latitude), lng: parseFloat(suggestion.longitude)});
        map.panTo({lat: parseFloat(suggestion.latitude), lng: parseFloat(suggestion.longitude)});
        map.setZoom(14);
    });

    // hide info window when text box has focus
    $("#q").focus(function(eventData) {
        info.close();
    });

    // re-enable ctrl- and right-clicking (and thus Inspect Element) on Google Map
    // https://chrome.google.com/webstore/detail/allow-right-click/hompjdfbfmmmgflfjdlnkohcplmboaeo?hl=en
    document.addEventListener("contextmenu", function(event) {
        event.returnValue = true; 
        event.stopPropagation && event.stopPropagation(); 
        event.cancelBubble && event.cancelBubble();
    }, true);

    //update UI
    update();

    
    // give focus to text box
    $("#q").focus();
}

/**
 * Removes markers from map.
 */

function removeMarkers()
{
    
    google.maps.event.addListener(map, "zoom_changed", function() {
        for (var i = 0; i < markers.length; i++){
            markers[i].setMap(null);
        }
        
    });
    
    google.maps.event.addListener(map, "dragstart", function() {
        for (var i = 0; i < markers.length; i++){
            markers[i].setMap(null);
        }
        
    });
    
     google.maps.event.addListener(map, "bounds_changed", function() {
        for (var i = 0; i < markers.length; i++){
            markers[i].setMap(null);
        }
        
    });
    
    markers = [];
}

/**
 * Searches database for typeahead's suggestions.
 */
function search(query, syncResults, asyncResults)
{
    // get places matching query (asynchronously)
    var parameters = {
        q: query
    };
    $.getJSON(Flask.url_for("search"), parameters)
    .done(function(data, textStatus, jqXHR) {
     
        // call typeahead's callback with search results (i.e., places)
        asyncResults(data);
        
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());

        // call typeahead's callback with no results
        asyncResults([]);
    });
}

/**
 * Shows info window at marker with content.
 */
function showInfo(marker, content)
{
    // start div
    var div = "<div id='info'>";
    if (typeof(content) == "undefined")
    {
        // http://www.ajaxload.info/
        div += "<img alt='loading' src='/static/ajax-loader.gif'/>";
    }
    else
    {
        div += "<ul>";
        for (var i=0; i<5; i++){
            div += "<li><a href=\"" + content[i].link + "\" target=\"_blank\">" + content[i].title + "</a></li>";
        }
        div += "</ul>";
    }

    // end div
    div += "</div>";

    // set info window's content
    info.setContent(div);

    // open info window (if not already open)
    info.open(map, marker);
}

/**
 * Updates UI's markers.
 */
function update() 
{
    // get map's bounds
    var bounds = map.getBounds();
    var ne = bounds.getNorthEast();
    var sw = bounds.getSouthWest();

    // get places within bounds (asynchronously)
    var parameters = {
        ne: ne.lat() + "," + ne.lng(),
        q: $("#q").val(),
        sw: sw.lat() + "," + sw.lng()
    };
    
    $.getJSON(Flask.url_for("update"), parameters)
    .done(function(data, textStatus, jqXHR) {

       // remove old markers from map
       removeMarkers();
       
    $("#q").focus(function(eventData) {
        
        info.close();
    });

       // add new markers to map
       for (var i = 0; i < data.length; i++)
       {
           //console.log(data.length);
           addMarker(data[i]);
           
       }
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());
    });
    
} 

