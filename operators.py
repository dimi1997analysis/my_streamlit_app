# = > < >= <= == !=
#logical operators : and, or, not

temp = float(input("enter temperatur : "))

if temp > 0 and temp <30 : 
    print("temperatur is normal")
#else : 
    #print("ist cold")
#elif temp < 0 or temp >= 30 :
    #print("stay home")
elif not(temp < 0 or temp >= 30) :
    #print("stay home")