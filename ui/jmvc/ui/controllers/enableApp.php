<html>
<input type="hidden" name="record_id" value="sadaasdas">
<input type="hidden" name="enabledApp" value="false">
</html>
<?php
/*  $conn = pg_pconnect("dbname=indivo");
if (!$conn) {
  echo "An error occurred.\n";
  exit;
}


  $link = pg_Connect("dbname=indivo user=indivo password=indivo");
  $result = pg_exec($link, "select * from indivo_allergy");
  $numrows = pg_numrows($result);
  echo "<p>link = $link<br>
  result = $result<br>
  numrows = $numrows</p>
  ";
print '<script type="text/javascript">'; 
print 'alert("test" )'; 
print '</script>';  
*/
$db = pg_connect("host=localhost port=5432 dbname=indivo user=indivo password=indivo");  
$query = "INSERT INTO indivo_enableApp VALUES ('$_POST['record_id']','$_POST[enabledApp]')";  
$result = pg_query($query);   
echo "testtttttttttttttt";
if (!$result)  
{  
echo "Update failed!!";  
} else  
{  
echo "Update successfull;";  
}
?>  

