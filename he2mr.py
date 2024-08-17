import struct
import json
import sys
debugMode = False

class read:
    def int(bytes, size): # Read integer
        value = int.from_bytes(bytes[:int(size/8)], "big") # Gets the value of the first int in the given bytes
        if debugMode: print(f"read.int() : bytes={bytes}, size={size}, value={value}")
        return value # Returns the value
    
    def float(bytes): # Read floating point
        value = struct.unpack(">f", bytes[:4])[0] # Gets the value of the first int in the given bytes
        if debugMode: print(f"read.float() : bytes={bytes}, value={value}")
        return value # Returns the value
    
    def bool(bytes): # Read boolean
        if bytes[0] == 0:
            return False 
        elif bytes[0] == 1:
            return True
        else:
            raise Exception("Unsupported value for boolean")
    
    def str(bytes): # Read string
        characters = []
        length = 0
        for c in bytes:
            if c != 0: # A 0, or \x00, represents the end of characters in a string
                characters.append(c.to_bytes().decode("utf-8")) # Decodes the byte to a UTF-8 character
                length += 1
            else:
                length = length + (4 - (length % 4)) # Extends the real length to the "real" end of the string - all strings are padded at the end with enough \x00's to bring the length to the next multiple of 4
                break # Stops processing bytes
        value = "".join(characters) # Converts all the decoded characters into one string
        if debugMode: print(f"read.str() : bytes={bytes}, value={value}, length={length}")
        return value, length # Returns the value, length and real length
    
    def strlist(bytes, items): # Read a list of strings, basically a string but with segments separated by \x00 or 0's
        stringlist = []
        length = 0
        index = 0
        for i in range(items):
            characters = []
            while True:
                byte = bytes[index]
                index += 1
                if byte != 0:
                    characters.append(byte.to_bytes().decode("utf-8")) # Decodes the byte to a UTF-8 character
                    length += 1
                else:
                    break
            stringlist.append("".join(characters))
        length += items - 1
        length = length + (4 - (length % 4))
        if debugMode: print(f"read.strlist() : bytes={bytes}, stringlist={stringlist}, length={length}")
        return stringlist, length

    def enum(bytes, enums): # Read enumerator
        choice = enums[bytes[0]]
        if debugMode: print(f"read.enum() : bytes={bytes}, enums={enums}, choice={choice}")
        return choice

print("----- he2materialreader v1.0 by LightningWyvern -----\nUsage: he2mr [path] [output - optional]\n")

try:
    filepath = sys.argv[1] # Get the file path of the file to analyse from the first command line argument
except:
    filepath = input("File Path : ") # Get the file path of the file to analyse

f = open(filepath, "rb") # Opens and stores the .material file

pointer = 0 # The pointer is to keep track of what bytes have been fully read/decoded/taken care of

if f.read(1) != b"\x80": # This sequence of bytes is identical in every .material file, so it being missing would indicate corruption, or the file isn't .material
    raise Exception("Material file is corrupted or broken")
pointer += 3
f.seek(2, 1)

f.seek(13, 1) # Skips 13 bytes with unknown purposes
pointer += 13

miragenodes = []
while True: # Loops through sections of data until it reaches the end of the list of nodes
    f.seek(2, 1) # Unknown data
    miragenodes.append({"DataSize": 0, "Value": 0, "Name": ""}) # Adds a data entry to the list

    # Reads and sets all the data
    miragenodes[-1]["DataSize"] = read.int(f.read(2), 16)
    miragenodes[-1]["Value"] = read.int(f.read(4), 32)
    miragenodes[-1]["Name"] = f.read(8).decode("utf-8")

    pointer += 16
    if read.int(f.read(4), 32) - 20 == pointer: # Finds the set of 4 bytes marking the end of the list
        break
    f.seek(pointer)

pointer += 16
f.seek(pointer)

# Read general material properties
materialflag = read.int(f.read(1), 8)
renderbackface = read.bool(f.read(1))
additiveblending = read.bool(f.read(1))
unknownflag = read.int(f.read(1), 8)
f.seek(3, 1)

texturecount = read.int(f.read(1), 8) # Gets number of textures in material

pointer += 20
f.seek(pointer)

(shader, subshader), shaderslength = read.strlist(f.read(), 2) # Gets the shader name and length
pointer += shaderslength
f.seek(pointer)

pointer += 4
f.seek(pointer)

propertypointers = [] # List of pointers to each property
while True:
    currentpointer = f.read(4) # Read a pointer
    pointer += 4
    if currentpointer == b"\x02\x00\x01\x00": # Marks the end of the list of pointers
        break # Stop reading
    else:
        propertypointers.append(read.int(currentpointer, 32)) # Add the pointer to the list
pointer += 8
f.seek(8, 1)

properties = []
for p in propertypointers:
    properties.append({"Name": "", "Flag1": 0, "Flag2": 0, "x": 0.0, "y": 0.0, "z": 0.0, "w": 0.0}) # Adds a data entry to the list
    properties[-1]["Name"], incrementpointer = read.str(f.read()) # Reads the name
    pointer += incrementpointer # Jumps to the end of the string
    f.seek(pointer)
    # Reads all the properties
    properties[-1]["x"] = round(read.float(f.read(4)), 4)
    properties[-1]["y"] = round(read.float(f.read(4)), 4)
    properties[-1]["z"] = round(read.float(f.read(4)), 4)
    properties[-1]["w"] = round(read.float(f.read(4)), 4)
    properties[-1]["Flag1"] = read.int(f.read(2), 16)
    properties[-1]["Flag2"] = read.int(f.read(2), 16)
    pointer += 28
    f.seek(pointer)

# Same thing as before, but there's always a property that's missing a pointer, so this handles that
f.seek(propertypointers[-1] + 28)
properties.append({"Name": "", "Flag1": 0, "Flag2": 0, "x": 0.0, "y": 0.0, "z": 0.0, "w": 0.0})
properties[-1]["Name"], incrementpointer = read.str(f.read())
pointer += incrementpointer
f.seek(pointer)
properties[-1]["x"] = round(read.float(f.read(4)), 4)
properties[-1]["y"] = round(read.float(f.read(4)), 4)
properties[-1]["z"] = round(read.float(f.read(4)), 4)
properties[-1]["w"] = round(read.float(f.read(4)), 4)
properties[-1]["Flag1"] = read.int(f.read(2), 16)
properties[-1]["Flag2"] = read.int(f.read(2), 16)
pointer += 20
f.seek(pointer)

#pointer += 12 # Skip past unknown data
f.seek(pointer)
if f.read()[12:].startswith(b"enable_multi_tangent_space"): # If the enable_multi_tangent_space parameter is present, skip an extra 32 bytes
    pointer += 48 # Skip past the enable_multi_tangent_space data
    emts = True
else:
    emts = False

pointer += (texturecount * 4) - 4
f.seek(pointer)

texturenames, incrementpointer = read.strlist(f.read(), texturecount) # Reads the list of texture names
pointer += incrementpointer

pointer += (texturecount * 4) + 12
textures = []

for n in texturenames:
    textures.append({"Name": n, "TextureName": "", "Type": "", "AddressU": "", "AddressV": "", "TexCoordIndex": ""}) # Creates a new data entry
    f.seek(pointer)
    (textures[-1]["TextureName"], textures[-1]["Type"]), incrementpointer = read.strlist(f.read(), 2) # Reads the texture filename
    pointer += incrementpointer + 4
    f.seek(pointer)
    # Reads other data
    textures[-1]["TexCoordIndex"] = read.int(f.read(1), 8)
    textures[-1]["AddressU"] = read.int(f.read(1), 8)
    textures[-1]["AddressV"] = read.int(f.read(1), 8)
    pointer += 8

# Puts data into a dictionary
outputdata = {
    "miragenodes": miragenodes,
    "general": {
        "materialflag": materialflag,
        "renderbackface": renderbackface,
        "additiveblending": additiveblending,
        "unknownflag1" : unknownflag
    },
    "shader": shader,
    "subshader": subshader,
    "parameters": properties,
    "enable_multi_tangent_space": emts,
    "textures": textures
}

f.close() # Closes the file

# Prints it in a readable json format
print(json.dumps(outputdata, indent=2))

try:
    write = open(sys.argv[2], "w") # Opens the file to output to, if it is requested in the 2nd argument
    write.write(json.dumps(outputdata, indent=2)) # Writes to the file
    write.close() # Closes the file
except:
    pass # Ignores if no file is given to write to

input("Press Enter to Continue")