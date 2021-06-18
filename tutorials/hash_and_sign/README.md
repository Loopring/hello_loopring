# Hash and Signature Tutorial

## hash example command
$python poseidon_hash_sample.py -a hash -i 1,2,3 
poseidon_hash [1, 2, 3]
hash of [1, 2, 3] is 20693456676802104653139582814194312788878632719314804297029697306071204881418

## Sign example command
$python poseidon_hash_sample.py  -a sign -i 1,2,3 -k 0x1
loopring sign message [1, 2, 3]
signature of '[1, 2, 3]' is 0x0b09268fe04061cdee982d1b7c99a99792409064e18f79ee7068ad66789a4c7000efa194cea14cbac78611bebafee72f08d18e8ee7f3dbdfe3a086d8729614ad0a57beb30e2d905618e2e4b73f9eec261957bf00c5c7788ecd1e0c3ec4fbaea9
