#create a substring from a string. string slicing
#index[]
#slice()
#[start:stop:step]

name = "dimitris panag"
first_name = name[0:8]
last_name = name[9:14]

#print(first_name + " " + last_name)
#print(last_name)
#crazy_name = name[::2]
#print(crazy_name)
#reversed_name = name[::-1]
#print(reversed_name)

url1 = "http://google.com"
url2 = "http://facebook.com"
url3 = "http://insta:com"

slice = slice(7,-4)
print(url1[slice])