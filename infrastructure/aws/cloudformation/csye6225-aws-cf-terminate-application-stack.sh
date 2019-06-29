echo  "stackname : $1"

echo "$stackname"


stack_delete=$(aws cloudformation delete-stack --stack-name $1)

echo "Stack is getting deleted...."

result=$(aws cloudformation wait stack-delete-complete --stack-name $1)

if [[ -z "result" ]]; then

  echo "---Stack has not been deleted---"

else

  echo "---Stack has been successfully deleted---"

fi
