#!/bin/bash
for var in $(sudo lsof -ti :5000)
do 
	sudo kill -9 $var
done

