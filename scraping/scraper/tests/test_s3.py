from scraper.document_store.s3 import S3DocumentStore

s3_store = S3DocumentStore(2000, (12000000, 14000000), bucket_name="iran-article-html-test")

# put_new_present and put_old successfully save file to S3
s3_store.put_new_present(200000, "test hahha")
s3_store.put_old(100000, "text lol")
s3_store.put_new_absent(1000)

for i in range(5):
    print("code returned by next_code(): " + str(s3_store.next_code()))

code_one = s3_store.next_code()
code_two = s3_store.next_code()
code_three = s3_store.next_code()
s3_store.put_error(code_one, "network error")
s3_store.put_error(code_two, "network error")
s3_store.put_error(code_three, "network error")
assert code_one == s3_store.next_code()
assert code_two == s3_store.next_code()
assert code_three == s3_store.next_code()

print("filename of new article file: " + s3_store.get_s3_filename(1000, new=True))
print("filename of old article file: " + s3_store.get_s3_filename(1000, new=False))
