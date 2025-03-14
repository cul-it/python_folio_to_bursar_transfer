# Charge Data format

Below you will find a sample of the JSON response that is returned when the charge endpoint is called. 
The response will contain a list of charges, errors and a summary of the charges. 


```JSON
{
    "charge_data": [
        {
            "amount": 500.0,
            "remaining": 2500.0,
            "status": {
                "name": "Open"
            },
            "paymentStatus": {
                "name": "Outstanding"
            },
            "feeFineType": "Lost item fee",
            "feeFineOwner": "Main Library",
            "title": "Library Laptop",
            "callNumber": "Extended Dell Loans",
            "barcode": "8917785698276",
            "materialType": "Laptop",
            "location": "Main",
            "metadata": {
                "createdDate": "2025-02-22T05:33:05.505+00:00",
                "updatedDate": "2025-02-22T05:33:05.505+00:00"
            },
            "dueDate": "2025-02-20T04:59:59.000+00:00",
            "loanId": "<<UUID>>",
            "userId": "<<UUID>>",
            "itemId": "<<UUID>>",
            "materialTypeId": "<<UUID>>",
            "feeFineId": "<<UUID>>",
            "ownerId": "<<UUID>>",
            "id": "<<UUID>>",
            "contributors": [],
            "loanPolicyId": "<<UUID>>",
            "overdueFinePolicyId": "<<UUID>>",
            "lostItemFeePolicyId": "<<UUID>>",
            "patron": {
                "username": "wz009",
                "id": "<<UUID>>",
                "externalSystemId": "9588628",
                "barcode": "111100095886281",
                "active": true,
                "patronGroup": "<<UUID>>",
                "departments": [
                    "<<UUID>>"
                ],
                "proxyFor": [],
                "personal": {
                    "lastName": "doe",
                    "firstName": "john",
                    "preferredFirstName": "john",
                    "email": "wz009@library.edu",
                    "addresses": [
                        {
                            "countryId": "USA",
                            "addressLine1": "No Address Supplied",
                            "city": "Somewhere",
                            "region": "NJ",
                            "postalCode": "98385",
                            "addressTypeId": "<<UUID>>",
                            "primaryAddress": true
                        }
                    ],
                    "preferredContactTypeId": "002",
                    "profilePictureLink": ""
                },
                "createdDate": "2025-01-24T16:32:10.447+00:00",
                "updatedDate": "2025-01-24T16:32:10.447+00:00",
                "metadata": {
                    "createdDate": "2021-06-24T21:27:02.515+00:00",
                    "createdByUserId": "<<UUID>>",
                    "updatedDate": "2025-01-24T16:32:10.440+00:00",
                    "updatedByUserId": "<<UUID>>",
                },
                "customFields": {
                    "college": "HZ",
                    "bursar": "opt_0",
                    "department": "Human Zone"
                }
            },
            "material": {
                "id": "<<UUID>>",
                "name": "Laptop",
                "source": "local",
                "metadata": {
                    "createdDate": "2021-06-17T19:22:28.570+00:00",
                    "createdByUserId": "<<UUID>>",
                    "updatedDate": "2021-06-17T19:22:28.570+00:00",
                    "updatedByUserId": "<<UUID>>",
                }
            },
            "cleanTitle": "Main Library Circulation Laptops",
            "fee_owner_id": "<<UUID>>|<<UUID>>",
            "owner_data": {
                "FeeFineOwner": "Main",
                "FeeFineName": "Lost item fee",
                "ChargeAccount": 72000000916,
                "ChargeDescription": "Main/Kr/Anx Lost Item Fee",
                "CreditAccount": 72100000916,
                "CreditDescription": "Main/Kr/Anx Lost Item Fee"
            }
        },
        
    ],
    "error_data": [
        {
            <<SAME data structure as charge_data>>
        },
    ],
    "summary": {
        "reportedRecordCount": 261,
        "uniquePatronCount": 50,
        "rawRecordCount": 100,
        "passedFineType": 100,
        "failedFineType": 0,
        "passedPatronType": 55,
        "failedPatronType": 45,
        "passedBursarActive": 155,
        "failedBursarActive": 5,
        "charge_total": 23907,
        "charge_remaining": 23907,
        "charge_record_count": 50,
        "charge_owner_stats": {
            "Main": {
                "name": "Main",
                "total": 13692,
                "remaining": 13692,
                "record_count": 26
            },
            "Location 2": {
                "name": "Location 2",
                "total": 5450,
                "remaining": 5450,
                "record_count": 7
            },
        },
        "errors_total": 7368,
        "errors_remaining": 7368,
        "errors_record_count": 50,
        "errors_owner_stats": {
            "Main": {
                "name": "Main",
                "total": 4950,
                "remaining": 4950,
                "record_count": 33
            },
            "Location 2": {
                "name": "Location 2",
                "total": 300,
                "remaining": 300,
                "record_count": 2
            },
        }
    }
}
```