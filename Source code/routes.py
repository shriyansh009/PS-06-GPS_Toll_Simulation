from flask import Flask, render_template ,render_template_string , request
from folium import plugins
import folium
import pandas as pd


#defining starting coordinate to variable (to represent start and end point)
wardha = (20.772678, 78.595530) # coordinate
karanja = (20.4983,77.47285) #coordinate
nagpur=(21.15235,79.08103)#coordinate


#method to display map on the html page
def paths():
    
   UMMlocation = (20.791828, 78.298535)
   m = folium.Map(location=UMMlocation, width="100%",height="100%", zoom_start=10)  # max zoom: 18
   # folium.CircleMarker(
   #  location=[20.791828, 78.298535],
   #  radius=100,
   #  fill=False,
   #  popup=folium.Popup("inline explicit Popup"),).add_to(m)


   # making marker to display route under toll zone (start/end)
   folium.Marker(location=wardha ,tooltip='Wardha',icon=folium.Icon(color='blue',icon='place')).add_to(m)
   folium.Marker(location=karanja,tooltip='karanja', icon=folium.Icon(color='red',icon='place')).add_to(m)
   folium.Marker(location=nagpur,tooltip='Nagpur' ,icon=folium.Icon(color='green',icon='place')).add_to(m)

   #read and write path1
   path2=pd.read_csv('paths/Nagpur_to_karanja.csv')
   polyline_cord=list(zip(path2["latitude"], path2["longitude"]))
   folium.PolyLine(locations=polyline_cord, weight=4, color='blue').add_to(m)
   
   #read and write path2
   path1=pd.read_csv('paths/nagpur_wardha.csv')
   polyline_cord=list(zip(path1["latitude"], path1["longitude"]))
   folium.PolyLine(locations=polyline_cord, weight=4, color='blue').add_to(m)
   
   #read and write path3
   path1=pd.read_csv('paths/wardha_karanja.csv')
   polyline_cord=list(zip(path1["latitude"], path1["longitude"]))
   folium.PolyLine(locations=polyline_cord, weight=4, color='blue').add_to(m)
   
   return m.get_root().render() 
