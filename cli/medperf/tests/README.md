# Testing Guidelines

The following are some instructions into how to write tests for Medperf. Medperf contains a lot of moving pieces, that all need to be tested to ensure code quality and robustness. If not done correctly, testing can (and has previously) become a daunting task. Therefore, the following text describes the philosophy being currently used at Medperf for writing tests efficiently.

## Testing Philosophy
- **Test the interface, not the implementation:** This works for several layers
  
  - If a class interface is provided, write tests for that interface and run those tests through all implementations.
  - Only test what is exposed by a given object. Private functions should be used by the public interface, so they'll get tested in the process.
  - If an object has more methods than its interface, test those separately. But, if that's the case you should <ins>_ask yourself if there's a way to separate that behavior (Design Patterns)_</ins>
- **Mock the state of surrounding objects, not function calls**: Surrounding objects are all the pieces that an interface interacts with to get the job done (e.g. The Entity interface interacts with the Comms interface).
  
  - Treat the function you're testing as a black box. We're only interested in what gets in vs what comes out. 
  - Instead of modifying the function behavior through mocks, mock the state that is expected for a function to work properly.
  - Instead of checking for function calls, check for state changes

## Testing Style
The following are some code style and structure tips to keep testing consistent

- **Implement a `setup` fixture to mock the state**: This setup fixture should be configurable and applicable to all tests for the given interface/instance.
  
  https://github.com/aristizabal95/medperf-2/blob/cfc9d3dda3bc0a9363ec5a6db33d69b0d68d005a/cli/medperf/tests/entities/test_entity.py#L27-L56
  
- **Keep states minimalistic**: Only recreate what is needed for a test to work. Don't overcomplicate your mocked state.
- **Group tests by method/functionality with classes**: By grouping tests is possible to share fixture configuration, and makes it easier to read both in code and through the IDE testing interface.
- **Move common test setup to class fixtures**: Another benefit of grouping tests by classes is that you can use class-specific fixtures. These can be used to move common configuration steps into a single location.

  https://github.com/aristizabal95/medperf-2/blob/cfc9d3dda3bc0a9363ec5a6db33d69b0d68d005a/cli/medperf/tests/entities/test_cube.py#L194-L202

- **Use describable names**: Tests are supposed to be self-documenting if done correctly. With a name that briefly describes what is being tested, accompanied by a clean implementation, tests become easy to read.

- **Use the Arrange, Act, Assert methodology**: This is a pattern widely used to keep tests minimal and consistent. If implemented properly, tests become slim and well-focused.

These guidelines are subject to change, and we're open to recommendations!