# ap-testsuite

A cli-based test suite for activitypub.

This is meant to approximate the test suite at [go-fed/testsuite](https://github.com/go-fed/testsuite).

# TODO

## Test cases

Vocab:

**Dereference** - Fully load JSON object.

    Retrieved JSON objects can include links to other JSON objects/resources
    on the server. Therefore, it is necessary to follow the links.

    {
        "object": "https://example.com/objects/test-object"
    }

    to

    {
        "object": {
            "foo": "bar"
        }
    }

### Common test cases
- Actor Cases
  
  Requires:
  - Actor ID

  Cases:
  - [ ] GET Actor
    
    Side effects:
    - Adds remote actor to the database

  - [ ] GET Actor Inbox

    Requires:
    - Actor in the database
    Side Effects:
    - Adds inbox to the database
    - Saves inbox id (used in later test cases)

  - [ ] Validate that Actor Inbox is OrderedCollection

    Requires:
    - Inbox in the database
    - Saved inbox id

- Object Cases

  Requires:
  - Object ID

  Cases:
  - [ ] Dereferences Object Id with ld+json plus profile

    `Accept: application/ld+json; profile="https://www.w3.org/ns/activitystreams"`

  - [ ] Dereferences Object Id with activity+json

    `Accept: application/activity+json`

- [ ] Deleted Object

  Requires:
  - ID of deleted Object
  - Are Tombstones enabled

  Logic:
  - Try to fetch object that has been deleted
  - Check error code.
    - `Tombstones?` => `410 Gone`
    - `No Tombstones.` => `404 Not Found`

- [ ] Invalid Object

  Requires:
  - ID of invalid Object

  Logic:
  - Try to fetch invalid object
  - Check that error code is `404 Not Found`

- [ ] Private Object

  Requires:
  - ID of private Object
  - Does server use `403 Forbidden`

  Logic:
  - Try to fetch private object
  - Check error code.
    - `Use 403` => `403 Forbidden`
    - `Otherwise` => `404 Not Found`

### Federating test cases
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