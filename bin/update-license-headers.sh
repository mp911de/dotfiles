YEAR=2020
for file in `find . -name '*.java' `; do sed -E -i '' "s/\* Copyright ([0-9]{4})-([0-9]{4}) the/\* Copyright \1-${YEAR} the/g" $file; done
for file in `find . -name '*.java' `; do sed -E -i '' "s/\* Copyright ([0-9]{4}) the/\* Copyright \1-${YEAR} the/g" $file; done

