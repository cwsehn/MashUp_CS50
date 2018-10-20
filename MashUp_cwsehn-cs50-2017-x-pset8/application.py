import os
import re
from flask import Flask, jsonify, render_template, request, url_for
from flask_jsglue import JSGlue

from cs50 import SQL
from helpers import lookup

# configure application
app = Flask(__name__)
JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")

@app.route("/")
def index():
    """Render map."""
    if not os.environ.get("API_KEY"):
        raise RuntimeError("API_KEY not set")
    return render_template("index.html", key=os.environ.get("API_KEY"))

@app.route("/articles")
def articles():
    """Look up articles for geo."""
    
    geo = request.args.get("geo")
    if len(geo) < 5:
        geo = "0" + geo
    
    look_list = lookup(geo)
    
    return jsonify(look_list)


@app.route("/search")
def search():
    """Search for places that match query."""

    q = (request.args.get("q"))
    
    #remove commas from query and add "protection" from inadvertent spaces....
    q = q.replace(",", " ")
    q = q.replace("   ", "  ")
    q = q.replace("  ", " ")
    q = q.strip()
    if "   " in q:
        return jsonify([])
    if q == "":
        return jsonify([])
        
    # added conveniences...
    q = q.replace("Ft.", "fort")
    q = q.replace("St.", "saint")
    q = q.replace("ft.", "fort")
    q = q.replace("st.", "saint")  
        
    # when q is a number....presumably the zip code....add leading zeroes to guarantee minimum of 5 digits...
    if q.isdigit():
        while len(q) < 5:
            q = "0" + q
        rows = db.execute("""SELECT * FROM places 
                            WHERE postal_code = :q """, q = (q))
        
        return jsonify(rows)
    
    else:
        qLength = len(q)
        count = 1
        spaces = 0
        spaceCount = [(0,0)] # a list of tuples!
        
        for l in q:
            # Python-ic string splicing ala [:] becomes a critical feature of this function from here forward
            if (l is " ") or (count == qLength):
                p = q
                # when q is just one word...presumably the name of the city...
                if count == qLength and spaces == 0:
                    rows = db.execute("""SELECT * FROM places 
                                    WHERE place_name 
                                    LIKE :q""", 
                                    q = (q + "%"))
                    
                    return jsonify(rows)
                    
                # when query is more than one word    
                elif count == qLength and spaces > 0:
                    
                    rows = db.execute("""SELECT * FROM places 
                                    WHERE place_name 
                                    LIKE :q""", 
                                    q = (q + "%"))
                                    
                    if len(rows) != 0:
                        return jsonify(rows) # entire query is multi-word city
                        
                    else:
                        # trim one word off the entire query at a time and test what remains for place_name match...
                        while spaces > 0:
                            p = p[:(spaceCount[spaces][1])] # p is the place_name going forward
                            
                            rows = db.execute("""SELECT * FROM places
                                                WHERE place_name
                                                LIKE :p""",
                                                p = (p + "%"))
                            
                            if len(rows) != 0:  # match found for place_name...
                                q = q[len(p)+1:]  # q becomes everything after the place_name w/o space between
                                break
                            
                            else: 
                                spaces -= 1
                                if spaces == 0:
                                    return jsonify(rows) # no city found...returns empty list
                                    
                    # after finding place_name (p)... and breaking from the while loop ...
                    # ...reset variables and test what remains of query (q)...  
                    qLength = len(q)
                    # in case of inadvertent single character.....revert to previous rows...
                    if qLength == 1:
                        return jsonify(rows)
                    count = 1
                    spaces = 0
                    spaceCount = [(0,0)]
                    for l in q:
                        if (l is " ") or (count == qLength):
                            r = q
                            
                            # when q is just one word...presumably the name of the state this time...
                            if count == qLength and spaces == 0:
                                
                                if len(q) == 2:
                                    # check for two-letter state abbreviation...
                                    rows = db.execute("""SELECT * FROM places 
                                                        WHERE place_name 
                                                        LIKE :p 
                                                        AND admin_code1 
                                                        LIKE :q""", 
                                                        p=(p+"%"), q=(q+"%"))
                                    
                                    if len(rows) != 0:
                                        return jsonify(rows)
                                        
                                    else:
                                        # in the unlikely occurance of city and country_code w/o state....
                                        rows = db.execute("""SELECT * FROM places
                                                            WHERE place_name
                                                            LIKE :p
                                                            AND country_code
                                                            LIKE :q""",
                                                            p=(p+"%"), q=(q+"%"))
                                        if len(rows) != 0:
                                            return jsonify(rows)
                                
                                elif len(q) >= 2:
                                    rows = db.execute("""SELECT * FROM places 
                                            WHERE place_name    
                                            LIKE :p 
                                            AND admin_name1 
                                            LIKE :q""", 
                                            p=(p +"%"), q=(q + "%"))
                                    
                                    #  city and full State name have been matched...
                                    # ...or returns empty list....
                                    return jsonify(rows)
                                    
                            elif count == qLength and spaces > 0:
                                rows = db.execute("""SELECT * FROM places 
                                                WHERE place_name 
                                                LIKE :p
                                                AND admin_name1
                                                LIKE :q""", 
                                                p=(p + "%"), q = (q + "%"))
                                    
                                if len(rows) != 0:
                                    return jsonify(rows) # remains of query is multi-word state
                                
                                else:
                                    space_holder = spaces
                                    # trim one word off the entire query at a time and test what remains for place_name match...
                                    while spaces > 0:
                                        
                                        r = r[:(spaceCount[spaces][1])] # r is the admin_name1 going forward
                                        rows = db.execute("""SELECT * FROM places
                                                            WHERE place_name
                                                            LIKE :p
                                                            AND admin_name1
                                                            LIKE :r
                                                            OR admin_code1
                                                            LIKE :r
                                                            AND place_name
                                                            LIKE :p""",
                                                            p=(p + "%"), r=(r + "%"))
                                        
                                        if len(rows) != 0:  # match found for admin_name1...(full state name)
                                            q = q[len(r)+1:]  # q becomes everything after the state name w/o space between
                                            # at this point whatever is after state is inconsequential....
                                            return jsonify(rows)
                                        
                                        else: 
                                            spaces -= 1
                                            if spaces == 0:
                                                
                                                return jsonify("is this it?") # no state name found...returns empty list...??
                            
                            elif l == " ":
                                spaces += 1
                                spaceCount.append((spaces, count-1))
                                count += 1
                                continue # ...ie back up to 'for l in q'
                            
                        else:
                            count += 1
                            
                # the positioning of this elif after all other conditions prevents 
                # ...the program from returning an error when inadvertent spaces are added to end of query...
                elif l == " ":
                    # multi-word city query....
                    spaces += 1
                    spaceCount.append((spaces, count-1))
                    count += 1
                    continue    
            else:
                count += 1


@app.route("/update")
def update():
    """Find up to 10 places within view."""

    # ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # explode southwest corner into two variables
    (sw_lat, sw_lng) = [float(s) for s in request.args.get("sw").split(",")]

    # explode northeast corner into two variables
    (ne_lat, ne_lng) = [float(s) for s in request.args.get("ne").split(",")]

    # find 10 cities within view, pseudorandomly chosen if more within view
    if (sw_lng <= ne_lng):

        # doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM places
            WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
            GROUP BY country_code, place_name, admin_code1
            ORDER BY RANDOM()
            LIMIT 10""",
            sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # crosses the antimeridian
        rows = db.execute("""SELECT * FROM places
            WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
            GROUP BY country_code, place_name, admin_code1
            ORDER BY RANDOM()
            LIMIT 10""",
            sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # output places as JSON
    return jsonify(rows)
