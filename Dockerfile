FROM python:3

RUN pip install opencv-contrib-python
RUN pip install Flask

COPY res /app/res
COPY static /app/static
COPY templates /app/templates
ADD constants.py /app/constants.py
ADD image_processor.py /app/image_processor.py
ADD main.py /app/main.py
ADD run.sh /app/run.sh

CMD ["./app/run.sh"]