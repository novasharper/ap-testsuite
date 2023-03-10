# ap-testsuite

A cli-based test suite for activitypub.

This is meant to approximate the test suite at [go-fed/testsuite](https://github.com/go-fed/testsuite).

# TODO

## General

- [x] Add support for configuring via config file instead of arguments
- [ ] Add auth support

  This is needed for Client2Server operations (e.g., getting the inbox)

  Auth Types:
  - [ ] OAuth flow (generate bearer token)
  - [ ] Cookie Auth
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
    - `Tombstones?` => `410 Gone`
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

  - [ ] Delivers all activities posted in the outbox
  - [ ] GET Actor outbox
  - [ ] Outbox contains delivered Activities
  - [ ] Uses `to` to determine delivery recipients
  - [ ] Uses `cc` to determine delivery recipients
  - [ ] Uses `bto` to determine delivery recipients
  - [ ] Uses `bcc` to determine delivery recipients
  - [ ] Provides and `id` in non-transient activities sent to other servers
  - [ ] Dereferences delivery targets with user's credentials
  - [ ] Delivers to Actors in Collections/OrderedCollections
  - [ ] Delivers to nested Actors in Collections/OrderedCollections
  - [ ] Delivers Create with Object
  - [ ] Delivers Update with Object
  - [ ] Delivers Delete with Object
  - [ ] Delivers Follow with Object
  - [ ] Delivers Add with Object and Target
  - [ ] Delivers Remove with Object and Target
  - [ ] Delivers Like with Object
  - [ ] Delivers Block with Object
  - [ ] Delivers Undo with Object
  - [ ] Does not double-deliver the same activity
  - [ ] Does not self-address an activity
  - [ ] Should not deliver blocks
  - [ ] Delivers create activity for artical to federated peer
  - [ ] Dedupes Actor inbox
  - [ ] Send a follow request for acceptance
  - [ ] Accept a follow request
  - [ ] Send a follow request for rejection
  - [ ] Reject a follow request
  - [ ] GET Followers collection
  - [ ] Receives Accept-Follow activity from federated peer
  - [ ] Receives Reject-Follow activity from federated peer
  - [ ] GET Following collection
  - [ ] Following collection has Accepted-Follow Actor
  - [ ] Following Collection does not have Rejected-Follow Actor
  - [ ] Send Activity with followers also addressed
  - [ ] Handles a reply requiring inbox forwarding
  - [ ] Applied inbox forwarding
  - [ ] Does not process update activity from unauthorized actor
  - [ ] Confirm whether unauthorized update applied

</p>
</details>
