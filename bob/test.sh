if [ "$#" -eq 0 ]; then
    python3 -m pytest ./ --cov
    echo "tested all "
fi
if [ "$#" -eq 1 ]; then
    python3 -m pytest $1/tests --cov=$1
    echo "tested" $1 "/"
fi
if [ "$#" -eq 2 ]; then
    python3 -m pytest $1/tests/test_$2.py --cov=$1
    echo "tested" $1 "/" $2
fi
if [ "$#" -eq 3 ]; then
    python3 -m pytest $1/tests/test_$2.py --cov=$1 --cov-report=html
    echo "tested" $1 "/" $2
    google-chrome ./htmlcov/$1_$3_py.html
fi