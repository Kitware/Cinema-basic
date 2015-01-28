
import re, os, json, argparse


# =============================================================================
# Return the ordered list of replaceable variable names
# =============================================================================
def getOrderedVariableNames(namePattern):
    regex = re.compile('{([^}]+)}')
    return regex.findall(namePattern)


# =============================================================================
# Build a path given a pattern string, and an object containing corresponding
# key-value pairs
# =============================================================================
def buildCinemaPath(namePattern, dictionary):
    regex = re.compile('{([^}]+)}')
    templateList = regex.split(namePattern)
    replaceList = []

    for piece in templateList:
        if piece in dictionary:
            replaceList.append(dictionary[piece])
        else:
            replaceList.append(piece)

    return ''.join(replaceList)


# =============================================================================
# Given a name pattern like "{time}/{theta}/{phi}/{filename}" (or similar) and
# a dictionary of values where the top-level keys in the dictionary should
# correspond to the strings within the '{' and '}' in the name pattern,
# generate tuples of the form (index, relative path).
# =============================================================================
def cinemaFileIterator(namePattern, arguments):
    compList = getOrderedVariableNames(namePattern)
    argumentList = []

    for comp in compList:
        argumentList.append(arguments[comp]['values'])

    maxIndices = [ len(argumentList[i]) - 1 for i in xrange(len(argumentList)) ]
    currentIndices = [ 0 for i in argumentList ]

    done = False
    idx = 0

    while not done:
        currentValues = { compList[i] : argumentList[i][currentIndices[i]] for i in xrange(len(currentIndices)) }
        yield idx, currentValues

        # try to increment our multi-base "counter" (the index list), and if
        # We have reached the top, then we break
        idx += 1
        for i in xrange(len(currentIndices) - 1, -1, -1):
            if currentIndices[i] < maxIndices[i]:
                currentIndices[i] += 1
                break
            else:
                if i == 0:
                    done = True
                currentIndices[i] = 0


# =============================================================================
# Main entry point
# =============================================================================
if __name__ == "__main__":
    description = "Test the cinema file iterator"

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--rootdir", type=str, default="", help="Path to root of data set (where info.json lives)")

    args = parser.parse_args()

    infojson = os.path.join(args.rootdir, 'info.json')

    json_data = None
    with open(infojson, 'r') as fd:
        json_data = json.load(fd)

    namePattern = json_data['name_pattern']
    arguments = json_data['arguments']

    count = 0

    for fileIdx, values in cinemaFileIterator(namePattern, arguments):
        relativePath = buildCinemaPath(namePattern, values)
        print fileIdx," => ",relativePath
        count += 1

    print "Found ",count," items"
