# ap-testsuite

A cli-based test suite for activitypub.

This is meant to approximate the test suite at [go-fed/testsuite](https://github.com/go-fed/testsuite).

# TODO

## General

- [x] Add support for configuring via config file instead of arguments
- [x] Add auth support

  Auth Types:
  - [x] HTTP Signature
  - [x] Cookie Auth
  - [x] Bearer token
  - [ ] OAuth flow (generate bearer token)
  - [ ] Password Auth

  NOTE: OAuth flow will likely require password/cookie support to generate
  bearer token.

## Test cases

<details><summary>Common test cases</summary>
<p>

- [x] Get Actor
  
  Requires:
  - Actor ID

  Logic:
  - Get actor based on id
  - Use 'outbox' field of actor to get actor outbox
  - Validate outbox object type. Must be one of:
    - `OrderedCollection`
    - `OrderedCollectionPage`
  - If outbox is an `OrderedCollectionPage`, get first page and validate
    that it is an `OrderedCollection`

- [x] Get Actor Inbox

  Requires:
  - Actor ID

  Logic:
  - Get actor based on id
  - Use 'inbox' field of actor to dereference inbox
  - Validate inbox type is `OrderedCollection` or `OrderedCollectionPage`

- [x] Get Object

  Validate that server supports both AS2 media types

  Requires:
  - Object ID

  Logic:
  - Get object with `ld+json` media type:

    `Accept: application/ld+json; profile="https://www.w3.org/ns/activitystreams"`

  - Get object with `activity+json` media type:

    `Accept: application/activity+json`

- [x] Deleted Object

  Requires:
  - ID of deleted Object
  - Are Tombstones enabled

  Logic:
  - Try to fetch object that has been deleted
  - Check error code.
    - `Tombstones?` => `410 Gone` + warn if body is not type `Tombstone`
    - `No Tombstones.` => `404 Not Found`

  TODO:
  - [ ] Need to find deleted object to validate that this works

- [x] Invalid Object

  Requires:
  - ID of invalid Object

  Logic:
  - Try to fetch invalid object
  - Check that error code is `404 Not Found`

- [x] Private Object

  Requires:
  - ID of private Object
  - Does server use `403 Forbidden`

  Logic:
  - Try to fetch private object
  - Check error code.
    - `Use 403` => `403 Forbidden`
    - `Otherwise` => `404 Not Found`

  TODO:
  - [ ] Need to find private object to validate that this works

</p>
</details>

<details><summary>Federating test cases</summary>
<p>

  - [x] Delivers all activities posted in the outbox
  - [x] GET Actor outbox
  - [x] Outbox contains delivered Activities
  - [x] Uses `to` to determine delivery recipients
  - [x] Uses `cc` to determine delivery recipients
  - [x] Uses `bto` to determine delivery recipients
  - [x] Uses `bcc` to determine delivery recipients
  - [x] Provides and `id` in non-transient activities sent to other servers
  - [x] Dereferences delivery targets with user's credentials
  - [x] Delivers to Actors in Collections/OrderedCollections
  - [x] Delivers to nested Actors in Collections/OrderedCollections
  - [x] Delivers Create with Object
  - [x] Delivers Update with Object
  - [x] Delivers Delete with Object
  - [x] Delivers Follow with Object
  - [x] Delivers Add with Object and Target
  - [x] Delivers Remove with Object and Target
  - [x] Delivers Like with Object
  - [x] Delivers Block with Object
  - [x] Delivers Undo with Object
  - [x] Does not double-deliver the same activity
  - [x] Does not self-address an activity
  - [x] Should not deliver blocks
  - [x] Delivers create activity for article to federated peer
  - [x] Dedupes Actor inbox
  - [x] Send a follow request for acceptance
  - [x] Accept a follow request
  - [x] Send a follow request for rejection
  - [x] Reject a follow request
  - [x] GET Followers collection
  - [x] Receives Accept-Follow activity from federated peer
  - [x] Receives Reject-Follow activity from federated peer
  - [x] GET Following collection
  - [x] Following collection has Accepted-Follow Actor
  - [x] Following Collection does not have Rejected-Follow Actor
  - [x] Send Activity with followers also addressed
  - [x] Handles a reply requiring inbox forwarding
  - [x] Applied inbox forwarding
  - [x] Does not process update activity from unauthorized actor
  - [x] Confirm whether unauthorized update applied

</p>
</details>
