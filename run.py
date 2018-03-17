import pandas as pd
import numpy as np
import time
import sys

battery_now = float(0)                         # the current capacity of the battery
min_peak_demand_15minute = sys.float_info.max   # answer

fd1 = pd.read_csv('./power consumption.csv');
fd2 = pd.read_csv('./generator.txt', sep=' ', header=None );


# set up battery performance 
max_bte = float(raw_input("Maximum battery energy (kWh): "))
min_bte = float(raw_input("Minimum battery energy (kWh): "))
max_charg = float(raw_input("Maximum battery power charging/discharge power (kW): "))
bte_n = float(raw_input("Battery charge/discharge efficiency (e.g. 0.8): "))


# using 1 hour as a basic unit
time_unit = (60*60)
# define how many units is 24 hours period
num_unit = (24*60*60) / time_unit


def samplingrate():   # define resampling rate in these two file
    timearray0 = time.strptime(fd1['Date/Time'][0], " %m/%d  %H:%M:%S") 
    timearray1 = time.strptime(fd1['Date/Time'][1], " %m/%d  %H:%M:%S") 
    timeStamp0 = int(time.mktime(timearray0))
    timeStamp1 = int(time.mktime(timearray1))
    t1 = timeStamp1 - timeStamp0
    
    timearray0 = time.strptime(fd2[0][0], "%Y-%m-%dT%H:%M:%S") 
    timearray1 = time.strptime(fd2[0][1], "%Y-%m-%dT%H:%M:%S") 
    timeStamp0 = int(time.mktime(timearray0))
    timeStamp1 = int(time.mktime(timearray1))
    t2 = timeStamp1 - timeStamp0

    return (time_unit/t1, time_unit/t2)
     
    pass


def if_solar_start(i, index):                                        # define whether the solar generation starts, and make two files timing consistency 
    fd1['Date/Time'][i] = fd1['Date/Time'][i].replace( '24:','00:') # use 00:00:00 instead of 24:00:00    
   
    timearray2 = time.strptime(fd2[0][index], "%Y-%m-%dT%H:%M:%S") 
    timelist = list(timearray2)                                            # make years between two files consistent
    str_year = str(timelist[0])
    timearray1 = time.strptime(str_year+fd1['Date/Time'][i], "%Y %m/%d  %H:%M:%S")  


    timeStamp1 = int(time.mktime(timearray1))
    timeStamp2 = int(time.mktime(timearray2))
    if( timeStamp1 >= timeStamp2):                               # whether the solar generation starts
        return True
    return False
    pass

def battery_b(demand):                                    # define battery behariour
    global battery_now, max_bte, minbte, max_charg, bte_n
    if(demand<0 and battery_now<max_bte):                 # generation larger than consumption, store the energy
        charge = -demand/4                               # 1/4 hour = 15 minute
        battery_now = battery_now + charge

        if(battery_now>max_bte):                           # the maximum capacity of the cattery
            battery_now=max_bte
        demand = 0

    elif(demand<0):                                       # generation larger than consumption, but battery is full
        demand = 0
    elif(demand>0 and battery_now>min_bte):               #  discharge
   
        if(battery_now - (demand/4) >= min_bte):

            demand = 0
            battery_now = battery_now - (demand/4)

        else:

            demand = (demand - ((battery_now - min_bte)*4))
            battery_now = min_bte

    return demand
    pass

def main():
     
    global min_peak_demand_15minute
    t_index = samplingrate()
    solar_index=0

    demand = 0
    for i in range(len(fd1['[kW](Hourly)'])/t_index[0]):
      load = np.sum( fd1['[kW](Hourly)'][i*t_index[0]:i*t_index[0]+t_index[0]]  )
      for k in range(4):                                                        # 4 * 15 minute = 1 hour 

        generating=0
        to_batter = 0
        if(if_solar_start(i, solar_index)):                                # whether solar generation starts
            for j in range(0, (t_index[1]/4) ):
                if (  (solar_index*t_index[1] +j) < len(fd2[1]) ):
                     to_battery = fd2[1][ solar_index*t_index[1] +j ] 

                if(to_battery>max_charg):                               # max charge/ =discharge power
                     to_battery=max_charg 
                generating = generating + to_battery

            generating = generating /  (t_index[1] / 4) 
            solar_index = solar_index + 1
  
        demand = load - (generating * bte_n )  # demand & "generagting" losing because of efficiency


        demand = battery_b(demand)   # store in the battery or discharge from the battery
        min_peak_demand_15minute = min (min_peak_demand_15minute, demand)
        demand_15minute=0
    min_peak_demand_15minute = min_peak_demand_15minute                    # power over 24 hours to power over 15 minutes
    print ("min_peak_demand_15minute = %.4f"% min_peak_demand_15minute)
    
    pass
    
    
if __name__ == '__main__':
    main()
