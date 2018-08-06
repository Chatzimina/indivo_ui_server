#!/usr/bin/python
# -*- coding: utf-8 -*-

import psycopg2
import sys


def main(record):
 con = None

 try:
     
     con = psycopg2.connect(database='indivo', user='indivo', password='indivo')    
    
     cur = con.cursor()
  

     cur.execute("INSERT INTO indivo_enabledApp VALUES(record,'true'")
     con.commit()
    

 except psycopg2.DatabaseError, e:
    
     if con:
         con.rollback()
    
     print 'Error %s' % e    
     sys.exit(1)
    
    
 finally:
    
     if con:
         con.close()
