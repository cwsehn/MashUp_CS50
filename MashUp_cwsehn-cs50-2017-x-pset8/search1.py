 q = (request.args.get("q"))
    
    q = q.replace(",", "")
    return jsonify(q)
    
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
            if (l is " " or l is ",") or (count == qLength):
                
                p = q
                # when q is just one word...presumably the name of the city...
                if count == qLength and spaces == 0:
                    rows = db.execute("""SELECT * FROM places 
                                    WHERE place_name 
                                    LIKE :q""", 
                                    q = (q + "%"))
                    
                    return jsonify(rows)
                    
                # when city name is more than one word    
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
                            
                            if len(rows) != 0:
                                q = q[len(p)+1:]  # q is what comes after the place_name w/o space between
                                count = 1
                                break
                            else: 
                                spaces -= 1
                                if spaces == 0:
                                    return jsonify(rows) # no city found...returns empty list
                        
                else:
                    # trim the space or comma off of the query...
                    q = q[:count-1] 
                    
                rows = db.execute("""SELECT * FROM places 
                                    WHERE place_name 
                                    LIKE :q""", 
                                    q = (q + "%"))
                
                if l is ",":
                    q = p[count+1:] # q is now everything after place_name ....w/o space between...
                    p = p[:count-1] # p becomes the place_name variable
                    count = 1
                    break
                
                # multi-word city names....
                elif l is " ":
                    spaces += 1
                    spaceCount.append((spaces, count-1))
                    count += 1
                    q = p  # q back to full query
                    continue
                    
            else:
                count += 1
        
        return jsonify(q)    
        # in the case of city plus State abbreviation
        if len(q) == 2:
            
            
            rows = db.execute("""SELECT * FROM places 
                                WHERE place_name 
                                LIKE :p 
                                AND admin_code1 
                                LIKE :q""", 
                                p=(p+"%"), q=(q+"%"))
                                
            return jsonify(rows)
        
        # check for additional input ...full state name or state name plus country code
        if len(q) > 2:
            return jsonify(q)
            qLength = len(q)
            spaces = 0
            spaceCount = [(0,0)]
            
            for l in q:
                if (l is " " or l is ",")  or (count == qLength):
                    
                    r = q
                    return jsonify(q)
                    if count == qLength:
                        
                        rows = db.execute("""SELECT * FROM places 
                                        WHERE place_name    
                                        LIKE :p 
                                        AND admin_name1 
                                        LIKE :q""", 
                                        p=(p +"%"), q=(q + "%"))
                        #  city and full State name have been matched...                 
                        return jsonify(rows)
                            
                    else:
                        # trim space or comma off of query...
                        q = q[:count-1]
                        
                    rows = db.execute("""SELECT * FROM places 
                                        WHERE place_name    
                                        LIKE :p 
                                        AND admin_name1 
                                        LIKE :q""", 
                                        p=(p +"%"), q=(q + "%"))
                        
                    # at this point either there is a match of city and state or comma is mis-placed
                    if l is ",":
                        return jsonify(rows)
                        
                    # multi-word state names....
                    elif l is " ":
                        if len(rows) != 0:
                            return jsonify(rows)
                        else:
                            spaces += 1
                            spaceCount.append((spaces, count-1))
                            count += 1
                            q = r  # q back to full query
                            return jsonify(count)
                            continue
                    
                    
                    
                    
                    
                    
                    else:
                        q = r[count:]
                        r = r[:count-1]
                        count = 1
                        if len(q) == 2:
                            rows = db.execute("""SELECT * FROM places 
                                                WHERE place_name 
                                                LIKE :p 
                                                AND admin_name1 
                                                LIKE :r 
                                                AND country_code 
                                                LIKE :q """, 
                                                p=(p+"%"), q=(q+"%"), r=(r+"%"))
                                
                        return jsonify(rows)
                        
                        
                
                else:
                    count += 1    
        
        return jsonify("no such place!") # this is for testing only....or maybe not....
