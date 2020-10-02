from googletrans import Translator
trans = Translator()

f = open('C:\\Users\\hp\\Desktop\\hello.txt', 'r')
contents = f.read()
result = trans.translate(contents, dest ='fr')
print(result.text)

my_file = open("this_is_file.txt","w+")
my_file.write(result.text)
