from flask import flash,render_template


#Method to allocate coordinate to the selected location
def coordinates_allot(loc):
  
  # Defining a dictionary to store location data
  locations = {
      "nagpur": ( 21.15235,79.08103),
      "wardha": ( 20.77272,78.59551),
      "karanja": ( 20.4983,77.47285)
  }
  
  lat= locations[loc][0]  
  lon = locations[loc][1] 

  return lat,lon




#method to allocate the dataset of selected module to the path file
def paths_allocated(loc1,loc2):
  if loc1=="nagpur" and loc2=="wardha":
     file1_path="paths/nagpur_wardha.csv"
     return file1_path
  elif loc1=="nagpur" and loc2=="karanja":
     file1_path="paths/Nagpur_to_karanja.csv"
     return file1_path
  elif loc1=="karanja" and loc2=="wardha":
     file1_path="paths/wardha_karanja.csv"
     return file1_path
  elif loc1=="karanja" and loc2=="nagpur":
     file1_path="paths/Nagpur_to_karanja.csv"
     return file1_path
  elif loc1=="wardha" and loc2=="nagpur":
     file1_path="paths/nagpur_wardha.csv"
     return file1_path
  elif loc1=="wardha" and loc2=="karanja":
     file1_path="paths/wardha_karanja.csv"
     return file1_path
  else:
     return render_template('simulate.html')











