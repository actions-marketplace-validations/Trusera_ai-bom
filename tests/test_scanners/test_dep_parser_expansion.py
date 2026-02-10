"""Tests for expanded dependency parser support (Cargo.toml, go.mod, Gemfile, etc.)."""



from ai_bom.scanners.code_scanner import CodeScanner


class TestCargoTomlParsing:
    """Test Cargo.toml (Rust) dependency parsing."""

    def test_parse_basic_cargo_deps(self, tmp_path):
        """Test parsing basic Cargo.toml dependencies."""
        cargo_content = """
[package]
name = "my-rust-app"
version = "0.1.0"

[dependencies]
async-openai = "0.14.0"
anthropic-sdk = "0.1.0"
tokio = "1.35.0"
"""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(cargo_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        # Should find async-openai and anthropic-sdk
        component_names = [c.name for c in components]
        assert "async-openai" in component_names or "async_openai" in component_names
        assert "anthropic-sdk" in component_names or "anthropic_sdk" in component_names

    def test_parse_cargo_with_version_spec(self, tmp_path):
        """Test parsing Cargo.toml with version specs."""
        cargo_content = """
[dependencies]
async-openai = { version = "0.14", features = ["streaming"] }
"""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(cargo_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert any("openai" in name.lower() for name in component_names)

    def test_parse_cargo_empty_deps(self, tmp_path):
        """Test parsing Cargo.toml with no AI dependencies."""
        cargo_content = """
[dependencies]
serde = "1.0"
tokio = "1.35.0"
"""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(cargo_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        # Should not find AI components from deps
        assert len(components) == 0


class TestGoModParsing:
    """Test go.mod (Go) dependency parsing."""

    def test_parse_basic_go_mod(self, tmp_path):
        """Test parsing basic go.mod dependencies."""
        go_mod_content = """
module myapp

go 1.21

require (
    github.com/sashabaranov/go-openai v1.17.9
    github.com/anthropics/anthropic-sdk-go v0.1.0
    github.com/gin-gonic/gin v1.9.1
)
"""
        go_file = tmp_path / "go.mod"
        go_file.write_text(go_mod_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "github.com/sashabaranov/go-openai" in component_names
        assert "github.com/anthropics/anthropic-sdk-go" in component_names

    def test_parse_go_mod_single_line(self, tmp_path):
        """Test parsing go.mod with single-line require."""
        go_mod_content = """
module myapp

require github.com/sashabaranov/go-openai v1.17.9
"""
        go_file = tmp_path / "go.mod"
        go_file.write_text(go_mod_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "github.com/sashabaranov/go-openai" in component_names


class TestGemfileParsing:
    """Test Gemfile (Ruby) dependency parsing."""

    def test_parse_basic_gemfile(self, tmp_path):
        """Test parsing basic Gemfile dependencies."""
        gemfile_content = """
source 'https://rubygems.org'

gem 'ruby-openai'
gem 'anthropic', '~> 0.1'
gem 'rails', '~> 7.0'
"""
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text(gemfile_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "ruby-openai" in component_names
        assert "anthropic" in component_names

    def test_parse_gemfile_double_quotes(self, tmp_path):
        """Test parsing Gemfile with double quotes."""
        gemfile_content = """
gem "ruby-openai", "~> 3.0"
"""
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text(gemfile_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "ruby-openai" in component_names


class TestPomXmlParsing:
    """Test pom.xml (Maven) dependency parsing."""

    def test_parse_basic_pom_xml(self, tmp_path):
        """Test parsing basic pom.xml dependencies."""
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project>
    <dependencies>
        <dependency>
            <groupId>com.langchain4j</groupId>
            <artifactId>langchain4j</artifactId>
            <version>0.27.0</version>
        </dependency>
        <dependency>
            <groupId>com.openai</groupId>
            <artifactId>openai-java</artifactId>
            <version>1.0.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
        </dependency>
    </dependencies>
</project>
"""
        pom_file = tmp_path / "pom.xml"
        pom_file.write_text(pom_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "com.langchain4j:langchain4j" in component_names or "langchain4j" in component_names

    def test_parse_pom_xml_without_version(self, tmp_path):
        """Test parsing pom.xml without version tags."""
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project>
    <dependencies>
        <dependency>
            <groupId>com.langchain4j</groupId>
            <artifactId>langchain4j</artifactId>
        </dependency>
    </dependencies>
</project>
"""
        pom_file = tmp_path / "pom.xml"
        pom_file.write_text(pom_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert any("langchain4j" in name for name in component_names)


class TestGradleParsing:
    """Test build.gradle (Gradle) dependency parsing."""

    def test_parse_basic_gradle(self, tmp_path):
        """Test parsing basic build.gradle dependencies."""
        gradle_content = """
plugins {
    id 'java'
}

dependencies {
    implementation 'com.langchain4j:langchain4j:0.27.0'
    implementation 'spring-ai:0.8.0'
    testImplementation 'junit:junit:4.13'
}
"""
        gradle_file = tmp_path / "build.gradle"
        gradle_file.write_text(gradle_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "com.langchain4j:langchain4j" in component_names or "langchain4j" in component_names
        assert "spring-ai" in component_names

    def test_parse_gradle_kotlin_dsl(self, tmp_path):
        """Test parsing build.gradle.kts (Kotlin DSL)."""
        gradle_kts_content = """
dependencies {
    implementation("com.langchain4j:langchain4j:0.27.0")
    implementation("spring-ai:0.8.0")
}
"""
        gradle_file = tmp_path / "build.gradle.kts"
        gradle_file.write_text(gradle_kts_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert any("langchain4j" in name for name in component_names)

    def test_parse_gradle_api_compile(self, tmp_path):
        """Test parsing Gradle with api and compile configurations."""
        gradle_content = """
dependencies {
    api 'com.langchain4j:langchain4j:0.27.0'
    compile 'spring-ai:0.8.0'
}
"""
        gradle_file = tmp_path / "build.gradle"
        gradle_file.write_text(gradle_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert len(component_names) > 0


class TestCsprojParsing:
    """Test .csproj (.NET) dependency parsing."""

    def test_parse_basic_csproj(self, tmp_path):
        """Test parsing basic .csproj PackageReferences."""
        csproj_content = """<?xml version="1.0" encoding="utf-8"?>
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Azure.AI.OpenAI" Version="1.0.0" />
    <PackageReference Include="Microsoft.SemanticKernel" Version="1.0.0" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
  </ItemGroup>
</Project>
"""
        csproj_file = tmp_path / "MyApp.csproj"
        csproj_file.write_text(csproj_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "Azure.AI.OpenAI" in component_names
        assert "Microsoft.SemanticKernel" in component_names

    def test_parse_csproj_google_ai(self, tmp_path):
        """Test parsing .csproj with Google AI package."""
        csproj_content = """<?xml version="1.0" encoding="utf-8"?>
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Mscc.GenerativeAI" Version="1.0.0" />
  </ItemGroup>
</Project>
"""
        csproj_file = tmp_path / "MyApp.csproj"
        csproj_file.write_text(csproj_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]
        assert "Mscc.GenerativeAI" in component_names

    def test_parse_csproj_no_ai_packages(self, tmp_path):
        """Test parsing .csproj with no AI packages."""
        csproj_content = """<?xml version="1.0" encoding="utf-8"?>
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
  </ItemGroup>
</Project>
"""
        csproj_file = tmp_path / "MyApp.csproj"
        csproj_file.write_text(csproj_content)

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        # Should not find AI components
        assert len(components) == 0


class TestMixedDependencyFiles:
    """Test scanning projects with multiple dependency file types."""

    def test_python_and_rust_deps(self, tmp_path):
        """Test scanning project with both Python and Rust dependencies."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("openai==1.0.0\nlangchain>=0.1.0\n")

        # Create Cargo.toml
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("""
[dependencies]
async-openai = "0.14.0"
""")

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]

        # Should find both Python and Rust packages
        assert "openai" in component_names
        assert "langchain" in component_names
        assert any("openai" in name.lower() for name in component_names)

    def test_java_and_dotnet_deps(self, tmp_path):
        """Test scanning project with Java and .NET dependencies."""
        # Create build.gradle
        gradle = tmp_path / "build.gradle"
        gradle.write_text("""
dependencies {
    implementation 'com.langchain4j:langchain4j:0.27.0'
}
""")

        # Create .csproj
        csproj = tmp_path / "App.csproj"
        csproj.write_text("""<?xml version="1.0"?>
<Project>
  <ItemGroup>
    <PackageReference Include="Microsoft.SemanticKernel" Version="1.0.0" />
  </ItemGroup>
</Project>
""")

        scanner = CodeScanner()
        components = scanner.scan(tmp_path)

        component_names = [c.name for c in components]

        # Should find both Java and .NET packages
        assert any("langchain4j" in name for name in component_names)
        assert "Microsoft.SemanticKernel" in component_names
