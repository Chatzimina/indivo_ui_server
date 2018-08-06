import psycopg2
import requests
import sys
import os

email=sys.argv[1]
account_id=''
record_id=''
#email = 'deletetest@email.com'
fact_id=''
print email
try:
           conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
#           conn.autocommit = True
           conn.set_isolation_level(0)
           conn.commit()
           cursor = conn.cursor()

except  psycopg2.DatabaseError, e:
           
	   print e

try:
           cursor.execute( "SELECT account_id FROM public.indivo_account where contact_email='"+email+"';")
#           cursor.execute( "SELECT id FROM indivo_record where created_at>='2017-12-04'" )
           conn.commit()
           accountres = cursor.fetchall()
	   if accountres:
              account_id = accountres[0][0]

except  psycopg2.DatabaseError, e:
           print e





print account_id

try:
	   cursor.execute( "SELECT id FROM indivo_record where owner_id= '"+account_id+"'")
#           cursor.execute( "SELECT id FROM indivo_record where created_at>='2017-12-04'" )
           conn.commit()
           result = cursor.fetchall()
           if result:
	      record_id = result[0][0]

except  psycopg2.DatabaseError, e:
           print e


print record_id

try:

           cursor.execute( "ALTER TABLE indivo_demographics DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "ALTER TABLE indivo_phashare DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "ALTER TABLE indivo_fact DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "ALTER TABLE indivo_fact DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "ALTER TABLE indivo_account DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "ALTER TABLE indivo_carenet DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "ALTER TABLE indivo_principal DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "ALTER TABLE indivo_carenetaccount DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "ALTER TABLE indivo_document DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "ALTER TABLE indivo_record DISABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e





#        if counter == 10:
 #       	break
 #       counter += 1

     
try:

           cursor.execute( "delete  FROM indivo_phashare where record_id='"+record_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "delete  FROM indivo_reqtoken where record_id='"+record_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e



try:

           cursor.execute( "delete  FROM indivo_reqtoken where record_id='"+record_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e



try:

           cursor.execute( "select id  FROM public.indivo_document where record_id='"+record_id+"'" )
           conn.commit()
	   demog = cursor.fetchall()

except  psycopg2.DatabaseError, e:
           print e


print "before for"
for d in demog:
  try:

           cursor.execute( "delete  FROM indivo_demographics where document_id='"+d[0]+"'" )
           conn.commit()


  except  psycopg2.DatabaseError, e:
           print e

print "after for" 
try:

           cursor.execute( "delete  FROM indivo_document where record_id='"+record_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "SELECT id, created_at, document_id, record_id FROM public.indivo_fact where record_id='"+record_id+"'" )
           conn.commit()
           result = cursor.fetchall()
	   if result:
	           fact_id = result[0][0]

except  psycopg2.DatabaseError, e:
           print e


print fact_id

try:
	   cursor.execute( "SELECT *  FROM public.indivo_procedure where fact_ptr_id='"+fact_id+"'" )
	   conn.commit()
	   result_row = cursor.fetchone()
	   if result_row:

             cursor.execute( "delete  FROM public.indivo_procedure where fact_ptr_id='"+fact_id+"'" )
             conn.commit()
           


except  psycopg2.DatabaseError, e:
           print e


print "before"
try:
	   cursor.execute( "SELECT *  FROM public.indivo_problem where fact_ptr_id='"+fact_id+"'" )
	   conn.commit()
	   result_row = cursor.fetchone()
	   print result_row
	   if result_row:
		  print "inside 1"

                  cursor.execute( "delete  FROM public.indivo_problem where fact_ptr_id='"+fact_id+"'" )
                  conn.commit()



except  psycopg2.DatabaseError, e:
           print e



try:
	cursor.execute( "SELECT *  FROM public.indivo_allergy where fact_ptr_id='"+fact_id+"'" )
	conn.commit()
	result_row = cursor.fetchone()
	print result_row
	if result_row:


           cursor.execute( "delete  FROM public.indivo_allergy where fact_ptr_id='"+fact_id+"'" )
           conn.commit()



except  psycopg2.DatabaseError, e:
           print e



try:
	 cursor.execute( "SELECT *  FROM public.indivo_measurements where fact_ptr_id='"+fact_id+"'" )
	 conn.commit()
	 result_row = cursor.fetchone()
	 print result_row
	 if result_row:
	  

           cursor.execute( "delete  FROM public.indivo_measurements where fact_ptr_id='"+fact_id+"'" )
           conn.commit()



except  psycopg2.DatabaseError, e:
           print e



try:
	cursor.execute( "SELECT *  FROM public.indivo_appointment where fact_ptr_id='"+fact_id+"'" )
	conn.commit()
	result_row = cursor.fetchone()
        print result_row
	if result_row:
	   print "inside appoi"
           cursor.execute( "delete  FROM public.indivo_appointment where fact_ptr_id='"+fact_id+"'" )
           conn.commit()



except  psycopg2.DatabaseError, e:
           print e



try:
	cursor.execute( "SELECT *  FROM public.indivo_medication where fact_ptr_id='"+fact_id+"'" )
	conn.commit()
	result_row = cursor.fetchone()
        print result_row
	if result_row:

	   print "isnide medic"
           cursor.execute( "delete  FROM public.indivo_medication where fact_ptr_id='"+fact_id+"'" )
           conn.commit()



except  psycopg2.DatabaseError, e:
           print e


try:
	cursor.execute( "SELECT *  FROM public.indivo_labresult where fact_ptr_id='"+fact_id+"'" )
	conn.commit()
	result_row = cursor.fetchone()
        print result_row
	if result_row:
	   print "inside lab"
           cursor.execute( "delete  FROM public.indivo_labresult where fact_ptr_id='"+fact_id+"'" )
           conn.commit()



except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "delete  FROM indivo_fact where record_id='"+record_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e






try:

           cursor.execute( "delete  FROM indivo_record where id='"+record_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "delete  FROM indivo_carenet where record_id='"+record_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "delete  FROM indivo_accountauthsystem where account_id='"+account_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "delete  FROM indivo_accesstoken where account_id='"+account_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "delete  FROM indivo_sessiontoken where user_id='"+account_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "delete  FROM indivo_notification where account_id='"+account_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e





try:

           cursor.execute( "delete  FROM indivo_record where owner_id='"+account_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e




try:

           cursor.execute( "delete  FROM indivo_carenetaccount where account_id='"+account_id+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e




print "before account"

try:
	   print "inside account"
           cursor.execute( "delete  FROM indivo_account where contact_email='"+email+"'" )
           conn.commit()
	   print "after edelete"
           rows_deleted = cursor.rowcount
           print rows_deleted
	   print "skata"
	   
except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "delete  FROM indivo_principal where email='"+email+"'" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e



try:

           cursor.execute( "ALTER TABLE indivo_demographics ENABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

try:

           cursor.execute( "ALTER TABLE indivo_phashare ENABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "ALTER TABLE indivo_fact ENABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e



try:

           cursor.execute( "ALTER TABLE indivo_document ENABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e


try:

           cursor.execute( "ALTER TABLE indivo_record ENABLE TRIGGER ALL;" )
           conn.commit()


except  psycopg2.DatabaseError, e:
           print e

