# Data used

- [NASA Mars Facts](https://science.nasa.gov/mars/facts/) Mars' day is about 24.6 Earth hours. The game compresses one sol into a 3 minute cycle in [EnvironmentManager.py](lib/EnvironmentManager.py).
- [NASA Mars Explorer](https://psg.gsfc.nasa.gov/apps/mars/) hourly surface temperatures for Syrtis Major (about -80C before dawn to -23C in the afternoon) inform the temperature profile and day/night lighting in [EnvironmentManager.py](lib/EnvironmentManager.py), then affect charge use and traction in [Rover.py](objects/Rover.py).

## Prototype mapping

The NASA-based time and temperature model from `main` is retained in
`experimental`. One 24.6-Earth-hour sol is compressed into 180 seconds; the
local solar clock displays 24 Martian hours per sol. The hourly reference
table is interpolated through the day and modulates battery consumption,
engine cooling and traction. Syrtis Major is a reference climate, not a
measurement at our Valles Marineris mission sites.

Storm frequency, solar flare frequency and the eight-second shutdown window,
engine limits, energy leak probability, battery drain/recharge rates, and the
20-minute oxygen budget are gameplay tuning values, not NASA measurements.
No live NASA API connection is required to run the prototype.
