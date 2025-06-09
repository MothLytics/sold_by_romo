@echo off
echo Resetting inventory and importing data
echo 3 > input.txt
echo inventario_completo.csv >> input.txt
python src/update_inventory.py < input.txt
echo Done!
pause
del input.txt
