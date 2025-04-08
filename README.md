# GPS Logger (Phone)

Tracking device

FastAPI backend supporting POST request and transforming it into Keelson position Message

Quick start

```sh
# Other devices 
python main.py

python3 main.py --connect tcp/localhost:7447 --mode client

# Development environment
fastapi dev main.py      

```


http://localhost/log?lat=45.0&longitude=32.3&time=2055&s=10


Example Outout 
```sh
INFO:     192.168.0.5:32820 - "POST /logg?lat=57.435858459211886&long=12.032482428476214&time=2025-03-20T20:48:25.900Z HTTP/1.1" 200 OK
Received POST lat: 57.43587153498083, long 12.032563565298915, time: 2025-03-20T20:47:27.834Z
Received POST request body: b'lat=57.43587153498083&lon=12.032563565298915&sat=0&desc=&alt=72.0&acc=7.0&dir=0.0&prov=gps&spd_kph=0.2520000010728836&spd=0.07&timestamp=1742503647&timeoffset=2025-03-20T21:47:27.834%2B01:00&time=2025-03-20T20:47:27.834Z&starttimestamp=1742499925&date=2025-03-20&batt=54.0&ischarging=false&aid=089db14317f6af11&ser=089db14317f6af11&act=&filename=20250320&profile=Default+Profile&hdop=0.4&vdop=0.8&pdop=1.0&dist=1062&'
Parsed body: {'lat': ['57.43587153498083'], 'lon': ['12.032563565298915'], 'sat': ['0'], 'alt': ['72.0'], 'acc': ['7.0'], 'dir': ['0.0'], 'prov': ['gps'], 'spd_kph': ['0.2520000010728836'], 'spd': ['0.07'], 'timestamp': ['1742503647'], 'timeoffset': ['2025-03-20T21:47:27.834+01:00'], 'time': ['2025-03-20T20:47:27.834Z'], 'starttimestamp': ['1742499925'], 'date': ['2025-03-20'], 'batt': ['54.0'], 'ischarging': ['false'], 'aid': ['089db14317f6af11'], 'ser': ['089db14317f6af11'], 'filename': ['20250320'], 'profile': ['Default Profile'], 'hdop': ['0.4'], 'vdop': ['0.8'], 'pdop': ['1.0'], 'dist': ['1062']}
Parsed body LAT: ['57.43587153498083']



{ 
    # POS
    'lat': '57.43596067652106', # Deg 
    'lon': '12.032632464542985', # Deg
    'sat': '27', 
    'alt': '74.0', # Meters 
    'acc': '4.0', # Meters 
    
    # Log / Annotation
    'desc': '',  # Description text with note icon in app

    # Position Source Satellite 
    'hdop': '0.4', 
    'vdop': '0.6', 
    'pdop': '0.8', 
    
    # Device ID
    'profile': 'Default+Profile', 

    # Time UTC
    'time': '2025-03-30T11:51:35.000Z', 
    
    # Trajectory over ground 
    'dir': '0.0', # deg
    'spd': '0.0',  m/s
    
    # Battery
    'batt': '45.0', # Percentage 
    'ischarging': 'true', 
    

    'dist': '11432' # meters


    
    # Not parsed to Keelson
    'timeoffset': '2025-03-30T13:51:35.000%2B02:00', 
    'timestamp': '1743335495', 
    'act': '', 
    'filename': '20250330', 
    'prov': 'gps', 
    'starttimestamp': '1743235240', 
    'date': '2025-03-30', 
    'aid': '089db14317f6af11', 
    'ser': '089db14317f6af11', 
    'spd_kph': '0.0', # w
    
}

```

