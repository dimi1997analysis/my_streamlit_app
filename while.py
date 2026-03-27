#name = ""
#age = ""

#while len(name)==0 :
    #name = input("enter your name: " )
#while len(age)==0 :
    #age = input("enter your age: ")
#print(f"hello  {name}")
#print(f"you are {age} years old")

while True :
    age = input("enter your age ")
    if age == " " :
        continue 

    age = int(age)

    if age <= 0 :
        print("error")
        continue
    print(f"your age is {age}")
    break