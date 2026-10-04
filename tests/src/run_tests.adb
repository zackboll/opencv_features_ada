with Ada.Command_Line;
with AUnit.Reporter.Text;
with AUnit.Run;
with Features_Tests;

procedure Run_Tests is
   function Run is new AUnit.Run.Test_Runner_With_Status (Features_Tests.Suite);
   Reporter : AUnit.Reporter.Text.Text_Reporter;
   Result : AUnit.Status;
   use type AUnit.Status;
begin
   Result := Run (Reporter);
   if Result /= AUnit.Success then
      Ada.Command_Line.Set_Exit_Status (Ada.Command_Line.Failure);
   end if;
end Run_Tests;
