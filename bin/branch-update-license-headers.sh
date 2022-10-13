MESSAGE="$1"
shift

git fetch

PUSHSPEC=""
for branch in "$@"
do
    echo "Processing branch $branch"
		git checkout $branch
		git rebase origin/$branch
		update-license-headers.sh
		git add *.java
		git commit -m "$MESSAGE"		
		PUSHSPEC="${PUSHSPEC} $branch"
done

echo pushing $PUSHSPEC
