import math
from lib.Survival import Survival
from lib.EnvironmentManager import EnvironmentManager
from objects.Rover import Rover


class GameSettings:
    # Risk for a fully cold engine at night, expressed over a 20-second window.
    leakWindow = 20.0
    specs = (
        ('leakTemperature','Energy leak threshold',-80,50,1,'C','Engine temperature below which a night leak is possible'),
        ('leakRange','Energy leak temperature range',1,60,1,'C','Cooling through this range increases the risk'),
        ('oxygenMinutes','Oxygen supply',1,120,1,'min','Starting oxygen budget for an attempt'),
        ('provisionsMinutes','Provisions supply',1,120,1,'min','Time to consume a full stock without replenishment'),
        ('stormChance','Sandstorm chance',0,100,1,'%','Chance per weather check (every 30 seconds)'),
        ('flareChance','Solar flare chance',0,100,1,'%','Chance per daylight check (every 45 seconds)'),
        ('leakChance','Maximum night leak chance',0,100,1,'%','Chance over 20 seconds; temperature and darkness modify it'),
        ('energyUse','Energy consumption',0,300,5,'%','100% = default drive and leak drain; weather still affects usage'),
        ('rechargeRate','Battery recharge speed',0,10,0.1,'%/s','Battery percentage points per second while charging in daylight'),
        ('provisionsGain','Provisions per water unit',1,100,1,'%','Provision percentage points restored by watering the plants')
    )
    defaults = {
        'leakTemperature': Rover.energyLeakTemperatureC,
        'leakRange': Rover.energyLeakTemperatureRangeC,
        'oxygenMinutes': Survival.oxygenDuration/60,
        'provisionsMinutes': Survival.foodDuration/60,
        'stormChance': EnvironmentManager.stormChance*100,
        'flareChance': EnvironmentManager.solarFlareChance*100,
        'leakChance': -math.expm1(-Rover.energyLeakEventRate*leakWindow)*100,
        'energyUse': Rover.energyConsumptionScale*100,
        'rechargeRate': Rover.stationaryRechargeRate,
        'provisionsGain': Survival.provisionsPerWater
    }

    @classmethod
    def current(cls):
        return dict(leakTemperature=Rover.energyLeakTemperatureC,
                    leakRange=Rover.energyLeakTemperatureRangeC,
                    oxygenMinutes=Survival.oxygenDuration/60,
                    provisionsMinutes=Survival.foodDuration/60,
                    stormChance=EnvironmentManager.stormChance*100,
                    flareChance=EnvironmentManager.solarFlareChance*100,
                    leakChance=-math.expm1(-Rover.energyLeakEventRate*cls.leakWindow)*100,
                    energyUse=Rover.energyConsumptionScale*100,
                    rechargeRate=Rover.stationaryRechargeRate,
                    provisionsGain=Survival.provisionsPerWater)

    @classmethod
    def apply(cls, values, survival=None):
        validated={}
        for key,_,minimum,maximum,_,_,_ in cls.specs:
            value=float(values[key])
            if not math.isfinite(value):raise ValueError('Settings must be finite numbers')
            validated[key]=min(maximum,max(minimum,value))
        oxygenElapsed=Survival.oxygenDuration-survival.oxygen if survival is not None else 0
        provisionsElapsed=(100-survival.food)/100*Survival.foodDuration if survival is not None else 0
        Rover.energyLeakTemperatureC=validated['leakTemperature']
        Rover.energyLeakTemperatureRangeC=validated['leakRange']
        Survival.oxygenDuration=validated['oxygenMinutes']*60
        Survival.foodDuration=validated['provisionsMinutes']*60
        EnvironmentManager.stormChance=validated['stormChance']/100
        EnvironmentManager.solarFlareChance=validated['flareChance']/100
        Rover.energyConsumptionScale=validated['energyUse']/100
        Rover.stationaryRechargeRate=validated['rechargeRate']
        Survival.provisionsPerWater=validated['provisionsGain']
        probability=validated['leakChance']/100
        Rover.energyLeakEventRate=(1e6 if probability>=1 else -math.log1p(-probability)/cls.leakWindow)
        if survival is not None:
            survival.oxygen=max(0,Survival.oxygenDuration-oxygenElapsed)
            survival.food=max(0,100-provisionsElapsed/Survival.foodDuration*100)
