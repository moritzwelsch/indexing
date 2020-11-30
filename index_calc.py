import time
from src.index_calculator import Index

index_weighting_interval = 3600

index = Index()
index.get_weighting()


start = time.time()
index.get_index_value()
print(index.index_value)
end = time.time()

print("Duration:", end - start)
