# Data used

- [NASA Mars Facts](https://science.nasa.gov/mars/facts/) Mars' day is about 24.6 Earth hours. The game compresses one sol into a 3 minute cycle in [EnvironmentManager.py](lib/EnvironmentManager.py).
- [NASA Mars Explorer](https://psg.gsfc.nasa.gov/apps/mars/) hourly surface temperatures for Syrtis Major (about -80C before dawn to -23C in the afternoon) inform the temperature profile and day/night lighting in [EnvironmentManager.py](lib/EnvironmentManager.py), then affect charge use and traction in [Rover.py](objects/Rover.py).